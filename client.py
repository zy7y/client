"""
部分代码来源：https://github.com/reorx/httpstat
"""
import json as pjson
import os
import subprocess
import tempfile
from typing import Dict, Any, Tuple, List, Union
from urllib.parse import urlencode

https_template = """
  DNS Lookup   TCP Connection   TLS Handshake   Server Processing   Content Transfer
[   {a0000}  |     {a0001}    |    {a0002}    |      {a0003}      |      {a0004}     ]
             |                |               |                   |                  |
    namelookup:{b0000}        |               |                   |                  |
                        connect:{b0001}       |                   |                  |
                                    pretransfer:{b0002}           |                  |
                                                      starttransfer:{b0003}          |
                                                                                 total:{b0004}
"""[1:]

http_template = """
  DNS Lookup   TCP Connection   Server Processing   Content Transfer
[   {a0000}  |     {a0001}    |      {a0003}      |      {a0004}     ]
             |                |                   |                  |
    namelookup:{b0000}        |                   |                  |
                        connect:{b0001}           |                  |
                                      starttransfer:{b0003}          |
                                                                 total:{b0004}
"""[1:]


def make_color(code):
    def color_func(s):
        tpl = '\x1b[{}m{}\x1b[0m'
        return tpl.format(code, s)

    return color_func


cyan = make_color(36)


class CurlResponse:

    def __init__(self):
        self.transfer_info = None
        self.headers = None
        self.status_code = 500
        self.data = None
        self.err = None
        self.transfer_text = None
        self.curl = None

    def __transfer_info_update(self, url, out):
        """httpstat"""
        d = pjson.loads(out)
        # convert time_ metrics from seconds to milliseconds
        for k in d:
            if k.startswith('time_'):
                v = d[k]
                # Convert time_ values to milliseconds in int
                if isinstance(v, float):
                    # Before 7.61.0, time values are represented as seconds in float
                    d[k] = int(v * 1000)
                elif isinstance(v, int):
                    # Starting from 7.61.0, libcurl uses microsecond in int
                    # to return time values, references:
                    # https://daniel.haxx.se/blog/2018/07/11/curl-7-61-0/
                    # https://curl.se/bug/?i=2495
                    d[k] = int(v / 1000)
                else:
                    raise TypeError('{} value type is invalid: {}'.format(k, type(v)))

        # calculate ranges
        d.update(
            range_dns=d['time_namelookup'],
            range_connection=d['time_connect'] - d['time_namelookup'],
            range_ssl=d['time_pretransfer'] - d['time_connect'],
            range_server=d['time_starttransfer'] - d['time_pretransfer'],
            range_transfer=d['time_total'] - d['time_starttransfer'],
        )
        self.transfer_info = d

        if url.startswith('https://'):
            template = https_template
        else:
            template = http_template

        def fmta(s):
            return cyan('{:^7}'.format(str(s) + 'ms'))

        def fmtb(s):
            return cyan('{:<7}'.format(str(s) + 'ms'))

        self.transfer_text = template.format(
            # a
            a0000=fmta(d['range_dns']),
            a0001=fmta(d['range_connection']),
            a0002=fmta(d['range_ssl']),
            a0003=fmta(d['range_server']),
            a0004=fmta(d['range_transfer']),
            # b
            b0000=fmtb(d['time_namelookup']),
            b0001=fmtb(d['time_connect']),
            b0002=fmtb(d['time_pretransfer']),
            b0003=fmtb(d['time_starttransfer']),
            b0004=fmtb(d['time_total']),
        )

    def set_attrs(self,
                  curl: List[str] = None,
                  out: Union[str, bytes] = None,
                  header_file: str = None,
                  body_file: str = None,
                  ):
        for index, el in enumerate(curl):
            if el in ["-H", "-d", "-F"]:
                curl[index + 1] = f"'{curl[index+1]}'"
        self.curl = " ".join(curl)
        try:
            self.__transfer_info_update(curl[-1], out)
            self.status_code = int(self.transfer_info.get("status_code", "500"))

            with open(header_file, 'r') as f:
                self.headers = f.read().strip()

            with open(body_file, 'r') as f:
                self.data = f.read().strip()
        except Exception as e:
            print(e)

    @property
    def text(self):
        return self.data

    def json(self):
        return pjson.loads(self.data)


DictAny = Dict[str, Any]
DictStr = Dict[str, str]


class CurlRequest:
    HTTP_METHODS = [
        'GET',
        'HEAD',
        'POST',
        'PUT',
        'DELETE',
        'CONNECT',
        'OPTIONS',
        'TRACE',
        'PATCH'
    ]

    def __init__(self, method: str,
                 url: str,
                 headers: DictStr = None,
                 params: DictAny = None,
                 data: DictAny = None,
                 json: DictAny = None,
                 file: List[DictStr] = None,
                 auth: Tuple[str, str] = None,
                 proxy: str = None,
                 proxy_auth: Tuple[str, str] = None,
                 ignore_ssl: bool = True,
                 is_redirects: bool = True,
                 limit_rate: str = None,
                 timeout: int = None):
        """
        https://zhuanlan.zhihu.com/p/661602561
        :param method: 请求方法
        :param url: 请求路径
        :param headers: 请求头
        :param params: 查询参数
        :param data: 表单参数支持文件
        :param json:
        :param file: 文件 [{文件参数:"文件路径"}]
        :param auth:
        :param proxy:代理
        :param proxy_auth: 代理认证
        :param is_redirects: 自动重定向
        :param limit_rate:
        :param timeout: 超时时间
        """
        self.url = url
        self.method = method
        self.params = params
        self.headers = headers
        self.data = data
        self.json = json
        self.file = file
        self.proxy = proxy
        self.proxy_auth = proxy_auth
        self.auth = auth
        self.ignore_ssl = ignore_ssl
        self.is_redirects = is_redirects
        self.limit_rate = limit_rate
        self.timeout = timeout

        self._curl_args = []

    def _check_url(self):
        if not self.url:
            assert False, "请求路径必填"

    def _check_method(self):
        if method := (self.method or "get"):
            self.method = method.upper()
        if self.method not in self.HTTP_METHODS:
            assert False, f"请求方法应在其中 {self.HTTP_METHODS}"
        self._curl_args += ["-X", self.method]

    def _handle_params(self):
        if self.params:
            self.url = f"{self.url}?{urlencode(self.params)}"
            self.data = None
            self.json = None

    def _handle_data(self):
        if self.data:
            if not self.file:
                self._curl_args.extend(["-d", urlencode(self.data)])
            else:
                for k, v in self.data.items():
                    self._curl_args.extend(["-F", urlencode({k: v})])
            self.json = None

    def _handle_json(self):
        if self.json:
            self._curl_args.extend(["-d", pjson.dumps(self.json)])

    def _handle_headers(self):
        if self.headers:
            for k, v in self.headers.items():
                self._curl_args.append(["-H", f"{k}: {v}"])
            if self.headers.get("Content-Type"):
                return

        if self.json:
            self._curl_args.extend(["-H", "Content-Type: application/json"])
        elif self.file:
            self._curl_args.extend(["-H", "Content-Type: multipart/form-data"])
        elif self.data:
            self._curl_args.extend(["-H", "Content-Type: application/x-www-form-urlencoded"])

    def _handle_limit_rate(self):
        if self.limit_rate:
            self._curl_args.extend(["--limit-rate", self.limit_rate])

    def _handle_auth(self):
        if self.auth:
            username, password = self.auth
            self._curl_args.extend(["--user", f"{username}:{password}"])

    def _handle_proxy(self):
        if self.proxy:
            self._curl_args.extend(["-x", self.proxy])

            if self.proxy_auth:
                username, password = self.proxy_auth
                self._curl_args.extend(["--proxy-user", f"{username}:{password}"])

    def _handle_timeout(self):
        if self.timeout:
            self._curl_args.extend(["--connect-timeout", self.timeout])

    def _handle_ignore_ssl(self):
        if self.ignore_ssl:
            self._curl_args.append("-k")

    def _handle_redirects(self):
        if self.is_redirects:
            self._curl_args.append("-L")

    def _handle_file(self):
        if self.file:
            for file in self.file:
                for k, v in file.items():
                    self._curl_args.extend(["-F", f"{k}=@{v}"])

    def handle_args(self):
        self._handle_headers()
        self._handle_params()
        self._handle_data()
        self._handle_json()
        self._handle_file()
        self._handle_auth()
        self._handle_proxy()
        self._handle_ignore_ssl()
        self._handle_redirects()
        self._handle_limit_rate()
        self._handle_timeout()

    def check_args(self):
        self._check_url()
        self._check_method()

    def curl_args(self):
        self.check_args()
        self.handle_args()
        self._curl_args.append(self.url)
        return self._curl_args


curl_format = """{
"time_namelookup": %{time_namelookup},
"time_connect": %{time_connect},
"time_appconnect": %{time_appconnect},
"time_pretransfer": %{time_pretransfer},
"time_redirect": %{time_redirect},
"time_starttransfer": %{time_starttransfer},
"time_total": %{time_total},
"speed_download": %{speed_download},
"speed_upload": %{speed_upload},
"remote_ip": "%{remote_ip}",
"remote_port": "%{remote_port}",
"local_ip": "%{local_ip}",
"local_port": "%{local_port}",
"status_code": "%{http_code}"
}"""


def __curl(cmd):
    resp_body = None
    resp_header = None
    response = CurlResponse()
    try:
        with tempfile.NamedTemporaryFile(delete=False) as resp_body, \
                tempfile.NamedTemporaryFile(delete=False) as resp_header:
            command = ["curl", '-w', curl_format, "-D", resp_header.name, "-o", resp_body.name, "-s", "-S"] + cmd
            p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            out = out.decode()
            err = err.decode()
            response.set_attrs(["curl", *cmd], out, resp_header.name, resp_body.name)
            # 错误
            if err:
                response.err = err
    except Exception as e:
        print(e)
    finally:
        if resp_body:
            os.remove(resp_body.name)
        if resp_header:
            os.remove(resp_header.name)

    return response


def request(method: str,
            url: str,
            headers: DictStr = None,
            params: DictAny = None,
            data: DictAny = None,
            json: DictAny = None,
            file: List[DictStr] = None,
            auth: Tuple[str, str] = None,
            proxy: str = None,
            proxy_auth: Tuple[str, str] = None,
            ignore_ssl: bool = True,
            is_redirects: bool = True,
            limit_rate: str = None,
            timeout: int = None) -> CurlResponse:
    """

    :param method: 请求方法
    :param url: 请求地址
    :param headers: 请求头
    :param params: 查询参数
    :param data: 表单
    :param json: 请求体
    :param file: 文件（未实现）
    :param auth: 认证
    :param proxy_auth:代理认证
    :param proxy: 代理
    :param ignore_ssl:
    :param is_redirects:
    :param limit_rate: 速率限制（字节） 例如 200k
    :param timeout: 连接超时时间
    :return:
    """
    curl_req = CurlRequest(method, url, headers, params, data, json, file,
                           auth, proxy, proxy_auth, ignore_ssl, is_redirects, limit_rate, timeout)
    cmd_args = curl_req.curl_args()
    return __curl(cmd_args)


__all__ = [request, CurlRequest, CurlResponse]
