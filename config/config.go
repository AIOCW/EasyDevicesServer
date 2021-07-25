package config

import (
	"gopkg.in/yaml.v2"
	"io/ioutil"
	"log"
)

type Conf struct {
	Name string `yaml:"name"` //yaml：yaml格式 enabled：属性的为enabled
	Password string `yaml:"password"`
	Host string `yaml:"host"`
	Port string `yaml:"port"`
	DavPath string `yaml:"dav_path"`
}

func (c *Conf) GetConf() *Conf {
	yamlFile, err := ioutil.ReadFile("config.yaml")
	if err != nil {
		log.Printf("yamlFile.Get err   #%v ", err)
	}

	err = yaml.Unmarshal(yamlFile, c)
	if err != nil {
		log.Fatalf("Unmarshal: %v", err)
	}
	return c
}