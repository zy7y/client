>使用[Req](https://req.cool/zh/), 获得请求各阶段耗时
## GET
```shell
./client -url https://httpbin.org/get
```
```shell
./client -url https://httpbin.org/get?a=a&b=b&c=c&d=d&e=e&key=value1&key=va
```
## POST
### json 请求体
```shell
./client -url https://httpbin.org/post -method post -json '{"username": "imroc"}' 
```
### 表单
```shell
./client -url https://httpbin.org/post -method post -data '{"username": "imroc"}' 
```
## 请求头
```shell
./client -url https://httpbin.org/get -header '{"my-custom-header": "My Custom Value","user": "imroc"}'
```
## 上传
```shell
./client -url https://httpbin.org/post -method post -data '{"username": "imroc"}' -file '{"readme":"README.md"}'
```

## 下载
```shell
./client -url https://httpbin.org/bytes/10000 -output demo.txt
```

## 结果
### success
```shell
# 成功


{"request":":authority: httpbin.org\r\n:method: POST\r\n:path: /post\r\n:scheme: https\r\ncontent-type: application/json; charset=utf-8\r\ncontent-length: 20\r\naccept-encoding: gzip\r\nuser-agent: req/v3 (https://github.com/imroc/req)\r\n\r\n{\"username\": \"imroc}","response":{"body":"{\n  \"args\": {}, \n  \"data\": \"{\\\"username\\\": \\\"imroc}\", \n  \"files\": {}, \n  \"form\": {}, \n  \"headers\": {\n    \"Accept-Encoding\": \"gzip\", \n    \"Content-Length\": \"20\", \n    \"Content-Type\": \"application/json; charset=utf-8\", \n    \"Host\": \"httpbin.org\", \n    \"User-Agent\": \"req/v3 (https://github.com/imroc/req)\", \n    \"X-Amzn-Trace-Id\": \"Root=1-640c42e3-47f3dd42068e6f2c1a9ebeac\"\n  }, \n  \"json\": null, \n  \"origin\": \"117.30.122.163\", \n  \"url\": \"https://httpbin.org/post\"\n}\n","header":{"Access-Control-Allow-Credentials":["true"],"Access-Control-Allow-Origin":["*"],"Content-Length":["464"],"Content-Type":["application/json"],"Date":["Sat, 11 Mar 2023 08:59:15 GMT"],"Server":["gunicorn/19.9.0"]},"status":"200 OK"},"trace":{"DNSLookupTime":17728167,"ConnectTime":956660666,"TCPConnectTime":325239792,"TLSHandshakeTime":612742292,"FirstResponseTime":424255375,"ResponseTime":180709,"TotalTime":1380721459,"IsConnReused":false,"IsConnWasIdle":false,"ConnIdleTime":0,"RemoteAddr":{"IP":"52.86.68.46","Port":443,"Zone":""}}}
```
### error
```shell
2023/03/11 17:01:32 errorGet "https://ht": dial tcp: lookup ht: no such host
```