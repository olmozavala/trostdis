#!/usr/bin/env python
# coding: utf-8

from selenium import webdriver
from selenium.webdriver.support import ui
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import numpy as np
import pandas as pd

import os, stat, sys
from os.path import join
from operator import itemgetter

from config_goes.ClassConfig_Example import get_config
from config_goes.params import *

def waiting_load(driver):
    wait = ui.WebDriverWait(driver, 10)
    #wait.until(page_is_loaded)
    
def page_is_loaded(driver):
    return driver.find_element_by_name("body") != None

def findpages(driver):
    pages = driver.find_element_by_xpath('/html/body/div[1]/div[5]/page/div[2]/form[1]/table/tbody/tr/td[2]').text
    npage = [int(s) for s in pages.split() if s.isdigit()][1:3]
    return npage

def getdates(driver, lasttable, npage):
    dates = np.empty(shape=(lasttable,1), dtype='datetime64[ns]')
    for jj in range(lasttable):
        dt = driver.find_element_by_xpath('/html/body/div[1]/div[5]/page/div[2]/form[2]/table[2]/tbody/tr[{}]/td[4]'.format(int(jj+2))).text
        dt = datetime.strptime(dt[:-4],'%Y-%m-%d %H:%M:%S')
        dates[jj] = np.datetime64(dt)
    return dates

def find_nearest(a, a0):
    idx = (np.abs(a - a0)).argmin()
    w = a.shape[1]
    i = idx // w
    j = idx - i * w
    return i



if __name__ == "__main__":
    config = get_config()
    user0 = config[CLASS.user0]
    pass0 = config[CLASS.pass0]
    dates = config[CLASS.dates]

    tdates = np.load(dates)['dates']
    ndate  = len(tdates)
    delta = np.timedelta64(1, 'h')
    ldate = pd.to_datetime(tdates - delta)
    udate = pd.to_datetime(tdates + delta)



    driver = webdriver.Firefox()
    # Log in
    driver.get('https://www.avl.class.noaa.gov/saa/products/classlogin?resource=%2Fsaa%2Fproducts%2Fsearch%3Fsub_id%3D0%26datatype_family%3DGVAR_IMG%26submit.x%3D29%26submit.y%3D0')
    userlogin = driver.find_element_by_xpath('//*[@id="contentArea"]/div/form/input[1]')
    userlogin.send_keys(user0)
    passlogin = driver.find_element_by_xpath('//*[@id="contentArea"]/div/form/input[2]')
    passlogin.send_keys(pass0)
    driver.find_element_by_xpath('//*[@id="contentArea"]/div/form/input[3]').click()
    waiting_load(driver)


    # Search files
    for ii in range(ndate):
        # Dates, extent and satellite
        driver.get('https://www.avl.class.noaa.gov/saa/products/search?sub_id=0&datatype_family=GVAR_IMG&submit.x=29&submit.y=0')
        waiting_load(driver)
        start_date = driver.find_element_by_xpath('//*[@id="start_date"]')
        start_date.clear()
        start_date.send_keys(str(ldate.date[ii]))
        start_time = driver.find_element_by_xpath('//*[@id="start_time"]')
        start_time.clear()
        start_time.send_keys(str(ldate.time[ii]))
        end_date = driver.find_element_by_xpath('//*[@id="end_date"]')
        end_date.clear()
        end_date.send_keys(str(udate.date[ii]))
        end_time =  driver.find_element_by_xpath('//*[@id="end_time"]')
        end_time.clear()
        end_time.send_keys(str(udate.time[ii]))
        select_sat = driver.find_element_by_xpath('//*[@id="G13"]')
        if select_sat.is_selected() == False:
            select_sat.click()
        scene_ext = driver.find_element_by_xpath('/html/body/div[1]/div[5]/table/tbody/tr[2]/td/form/div[4]/table/tbody/tr/td[1]/input[3]')
        if scene_ext.is_selected() == False:
            scene_ext.click()

        driver.find_element_by_xpath('//*[@id="searchbutton"]').click()
        waiting_load(driver)

        # Select best file
        npage = findpages(driver)
        lasttable = 10 - (npage[0]*10 - npage[-1])
        dates = getdates(driver, lasttable, npage)
        mark = find_nearest(dates, tdates[ii])
        driver.find_element_by_xpath('/html/body/div[1]/div[5]/page/div[2]/form[2]/table[2]/tbody/tr[{}]/td[2]/input'.format(int(mark+2))).click()
        driver.find_element_by_xpath('/html/body/div[1]/div[5]/page/div[2]/form[2]/table[1]/tbody/tr/td[2]/input[2]').click()

    # Setup order
    driver.find_element_by_xpath('/html/body/div[1]/div[5]/page/div[2]/form[2]/table[1]/tbody/tr/td[2]/input[1]').click()
    # Order format
    driver.find_element_by_xpath('/html/body/div[1]/div[5]/form[2]/table[2]/tbody/tr[2]/td/table/tbody/tr[3]/th[5]/select/option[2]').click()
    # Bands (click to omit band)
    driver.find_element_by_xpath('/html/body/div[1]/div[5]/form[2]/table[2]/tbody/tr[2]/td/table/tbody/tr[3]/th[9]/select/option[1]').click()
    driver.find_element_by_xpath('/html/body/div[1]/div[5]/form[2]/table[2]/tbody/tr[2]/td/table/tbody/tr[3]/th[9]/select/option[2]').click()
    #driver.find_element_by_xpath('/html/body/div[1]/div[5]/form[2]/table[2]/tbody/tr[2]/td/table/tbody/tr[3]/th[9]/select/option[3]').click()
    #driver.find_element_by_xpath('/html/body/div[1]/div[5]/form[2]/table[2]/tbody/tr[2]/td/table/tbody/tr[3]/th[9]/select/option[4]').click()
    #driver.find_element_by_xpath('/html/body/div[1]/div[5]/form[2]/table[2]/tbody/tr[2]/td/table/tbody/tr[3]/th[9]/select/option[5]').click()

    # Place order
    driver.find_element_by_xpath('/html/body/div[1]/div[5]/form[2]/div[2]/input[1]').click()
    waiting_load(driver)

    # Fill survey
    driver.find_element_by_xpath('/html/body/div[1]/div[5]/page/mid/page/table/tbody/tr[2]/td/form/input[2]').click()
    driver.find_element_by_xpath('//*[@id="postSurvey"]').click()
    waiting_load(driver)
    driver.close()

