#!/usr/bin/python

import sys, getopt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import urllib
import fnmatch
import re
import os
import getpass

baseUrl = 'https://www.coursera.org'

def makeDir(directory):
  if not os.path.exists(directory):
    os.makedirs(directory)
    return directory
  else:
    return None

def scrapeWeek(driver, weekUrl, directory):
  print("Opening: " + weekUrl)
  driver.get(weekUrl)
  time.sleep(5)
  # get links to each topic
  weekSoup = BeautifulSoup(driver.page_source, 'lxml')
  for index, link in enumerate(weekSoup.findAll("a", {"class":"rc-ItemLink"})):
    topicUrl = baseUrl + link['href']
    topicDir = directory + str(index+1) + "_" + topicUrl.split("/")[-1]+ "/"
    if makeDir(topicDir) is not None:
      scrapeTopic(driver, topicUrl, topicDir)
    else:
      print(topicDir + " scraped")

def scrapeTopic(driver, topicUrl, directory):
  print("Opening: " + topicUrl)
  # get links to each resource
  driver.get(topicUrl)
  time.sleep(5)

  topicSoup = BeautifulSoup(driver.page_source, 'lxml')
  resourceLinks = topicSoup.findAll("a", {"class":["resource-link", "cml-asset-link"]})
  if len(resourceLinks) == 0:
    content = topicSoup.find("div", {"class":"content-container"})
    filename = directory + "content.html"
    if content is not None:
      html = content.prettify("utf-8")
      print("Downloading: " + filename)
      with open(filename, "wb") as file:
        file.write(html)
  for link in resourceLinks:
    url = link['href']
    urlre = '^http'
    if not re.search(urlre, url):
      url = baseUrl + url
    # get filename from url, if none, get from download attribute
    filename = url.split("?")[0].split("/")[-1]
    if not fnmatch.fnmatch(filename, '*.*') and link.has_attr('download'):
      filename = link['download']
    filename = directory + filename
    print("Downloading: " + filename)
    for attempt in range(5):
      try:
        urllib.request.urlretrieve(url, filename)
      except urllib.error.ContentTooShortError:
        pass
      else: 
        break
    else:
      with open(filename+"_error", "wb") as file:
        file.write("error while downloading")

def main(argv):

  email = input("Please your coursera username(email): ")
  # password = input("Please enter your password: ")
  password = getpass.getpass("Please enter your password: ")

  authSuffix = '?authMode=login'
  sourceURL = ''
  try:
      opts, args = getopt.getopt(argv,"hs:",["source="])
  except getopt.GetoptError:
    print('scrapper2.py -s <course_link>')
    sys.exit(2)
  for opt, arg in opts:
    if opt == '-h':
      print('scrapper2.py -u <course_link>')
      sys.exit()
    elif opt in ("-s", "--source"):
       sourceURL = arg

  # driver = webdriver.PhantomJS(executable_path=<PHANTOMJS_DRIVER_PATH>)
  driver = webdriver.Chrome(executable_path='../webdriver/chromedriver')
  driver.get(sourceURL + authSuffix)
  time.sleep(1)
  loginSoup = BeautifulSoup(driver.page_source, 'lxml')

  # login
  loginFrom = loginSoup.find("div", {"class":"rc-LoginForm"})
  loginURL=loginFrom.form['action']
  emailTextBox = driver.find_element_by_name("email")
  passwordTextBox = driver.find_element_by_name("password")
  emailTextBox.send_keys(email)
  passwordTextBox.send_keys(password)
  passwordTextBox.submit()
  time.sleep(5)

  course_directory = "results/" + re.findall(r'(?<=learn\/).*?(?=\/home)', sourceURL)[0]

  # get links to different weeks
  week1Soup = BeautifulSoup(driver.page_source, 'lxml')
  for index, link in enumerate(week1Soup.findAll("a", {"class":"rc-WeekItem"})):
    print(link['href'])

  for index, link in enumerate(week1Soup.findAll("a", {"class":"rc-WeekItem"})):
    weekUrl = baseUrl + link['href']
    print("Week URL: " + weekUrl)
    directory = course_directory + "/" + "week" + str(index+1) + "/"
    makeDir(directory)
    scrapeWeek(driver, weekUrl, directory)

  time.sleep(2)
  driver.close()

if __name__ == "__main__":
  main(sys.argv[1:])
