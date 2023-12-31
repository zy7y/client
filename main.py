from client import request

base_url = "http://127.0.0.1:8002"

# GET 查询参数
resp = request("get", base_url + "/get-params", params={"name": "Django"})
print(resp.text, resp.curl)

# GET 表单参数
resp = request("get", base_url + "/get-form", data={"name": "D"})
print(resp.text, resp.curl)

# POST 请求表单
resp = request("post", base_url + "/post-form", data={"name": "D", "ages": ["1", "3"]})
print(resp.json(), resp.curl)

# POST 文件上传(单文件)
resp = request("post", base_url + "/post-file", file=[{"name": "main.py"}])
print(resp.text, resp.curl)

# POST 多文件
resp = request("post", base_url + "/post-files", file=[
    {"files": "main.py"},
    # type后面是类型
    {"files": "client.py;type=text/x-python-script"},
])
print(resp.text, resp.curl)

# POST 表单 + 文件
resp = request("post", base_url + "/post-form-file",
               data={"name": "GGBond", "ages": ["1", "3"]},
               file=[{"file": "client.py;type=text/x-python-script"}
                     ])
print(resp.text, resp.curl)

# POST json
resp = request("post", base_url + "/post-json", json={"name": "22"})
print(resp.text, resp.curl)
