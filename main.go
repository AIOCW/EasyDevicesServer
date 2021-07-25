package main

import (
	. "awesomeProject/config"
	"flag"
	"fmt"
	"golang.org/x/net/webdav"
	"net/http"
)

func main() {
	var c Conf
	c.GetConf()
	fmt.Println("Name:" + c.Name)
	fmt.Println("Password:" + c.Password)
	fmt.Println("Host:" + c.Host)
	fmt.Println("Port:" + c.Port)
	fmt.Println("DavPath:" + c.DavPath)

	var addr *string
	var path *string
	//
	addr = flag.String("addr", c.Host+":"+c.Port, "")
	path = flag.String("path",  c.DavPath, "")
	fmt.Println(*addr)
	fmt.Println(*path)
	flag.Parse()

	fs := &webdav.Handler{
		FileSystem: webdav.Dir(*path),
		LockSystem: webdav.NewMemLS(),
	}

	http.HandleFunc("/", func(w http.ResponseWriter, req *http.Request) {
		// 获取用户名/密码
		username, password, ok := req.BasicAuth()
		if !ok {
			w.Header().Set("WWW-Authenticate", `Basic realm="Restricted"`)
			w.WriteHeader(http.StatusUnauthorized)
			return
		}
		// 验证用户名/密码
		if username != c.Name || password != c.Password {
			http.Error(w, "WebDAV: need authorized!", http.StatusUnauthorized)
			return
		}
		fs.ServeHTTP(w, req)
	})

	fmt.Println("addr=", *addr, ", path=", *path)
	http.ListenAndServe(*addr, nil)
}
