package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"github.com/imroc/req/v3"
	"log"
	"reflect"
	"strings"
)

// string2Map
//
//	@Description: 字符串转map
//	@param str 字符串 {"name":"7y"}
//	@return map[string]string
func string2Map(str string) map[string]string {
	if !json.Valid([]byte(str)) {
		panic("invalid json string")
	}
	var data map[string]string
	err := json.Unmarshal([]byte(str), &data)
	if err != nil {
		panic(err)
	}
	return data
}

func strJson2Map(str string) map[string]interface{} {
	var data map[string]interface{}
	err := json.Unmarshal([]byte(str), &data)
	if err != nil {
		panic(err)
	}
	return data
}

// uploadFileCallback
//
//	@Description: 上传文件回调函数输出
//	@param info
func uploadFileCallback(info req.UploadInfo) {
	fmt.Printf("%q uploaded %.2f%%\n", info.FileName, float64(info.UploadedSize)/float64(info.FileSize)*100.0)
}

/*
*
下载文件 回调
*/
func downloadFileCallback(info req.DownloadInfo) {
	if info.Response.Response != nil {
		fmt.Printf("downloaded %.2f%%\n", float64(info.DownloadedSize)/float64(info.Response.ContentLength)*100.0)
	}
}

func map2JsonString(info map[string]interface{}) string {
	result, err := json.Marshal(info)
	if err != nil {
		log.Fatal(err)
		return "{}"
	}
	return string(result)

}

// request 请求接口
//
//	@Description:
//	@param url 请求地址
//	@param method 请求方法
//	@param header 请求header {"name":"age"}
//	@param data 表单数据 {"name":"age"}
//	@param json body数据 {"name": "age"}
//	@param file 上传文件 {"参数": "文件地址"}
//	@param outPut 下载文件 文件保存地址
func request(url, method, header, data, json, file, outPut string) {
	var reqBuf bytes.Buffer

	client := req.C().
		EnableTraceAll().
		EnableDumpAll().
		EnableDumpEachRequestWithoutRequest().
		SetCommonDumpOptions(&req.DumpOptions{
			RequestOutput: &reqBuf,
			RequestHeader: true,
			RequestBody:   true,
		})
	reqClient := client.R()

	method = strings.Title(strings.ToLower(method))

	if header != "" {
		jsonHeader := string2Map(header)
		reqClient.SetHeaders(jsonHeader)
	}

	if outPut != "" && method == "Get" {
		reqClient.SetOutputFile(outPut).SetDownloadCallback(downloadFileCallback)
	}

	if file != "" {
		files := string2Map(file)
		reqClient.SetFiles(files).SetUploadCallback(uploadFileCallback)
	}

	if data != "" && json == "" {
		formData := string2Map(data)
		reqClient.SetFormData(formData)
		//reqClient.SetFormDataFromValues() 一个key 设置多个value
	}

	if json != "" && data == "" {
		reqClient.SetBodyJsonString(json)
	}

	// 获取方法 GET or POST等
	httpMethod := reflect.ValueOf(reqClient).MethodByName(method)

	if httpMethod.IsValid() {
		params := []reflect.Value{reflect.ValueOf(url)}
		result := httpMethod.Call(params)
		resp := result[0].Interface().(*req.Response)
		if result[1].Interface() != nil {
			log.Fatal("error", result[1])
		}

		info := map[string]interface{}{
			"request": reqBuf.String(),
			"response": map[string]interface{}{
				"status": resp.Status,
				"header": resp.Header,
				"body":   resp.String(),
			},
			"trace": resp.TraceInfo(),
		}
		fmt.Println(map2JsonString(info))
	} else {
		log.Fatal("请求方式不存在")
	}

}

func main() {
	// 定义参数变量
	var url, method, header, data, jsonData, file, output string
	// 定义命令行参数
	flag.StringVar(&url, "url", "", "请求的 URL")
	flag.StringVar(&method, "method", "GET", "请求的 HTTP 方法")
	flag.StringVar(&header, "header", "", "请求头，格式为 {'name': 'age'}")
	flag.StringVar(&data, "data", "", "表单数据")
	flag.StringVar(&jsonData, "json", "", "POST 请求的 JSON 数据")
	flag.StringVar(&file, "file", "", "POST 请求的文件路径")
	flag.StringVar(&output, "output", "", "GET 请求下载保存的文件路径")
	flag.Parse()
	request(url, method, header, data, jsonData, file, output)
}
