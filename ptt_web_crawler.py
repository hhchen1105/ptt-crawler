#!/usr/bin/env python

'''
Modified from bruce3557/PTT-Crawler: https://github.com/bruce3557/PTT-Crawler
'''

# Hung-Hsuan Chen <hhchen@psu.edu>
# Creation Date : 05-21-2014
# Last Modified: Wed May 28 21:27:49 2014

import gflags
import json
from lxml import etree as letree
import mechanize
import os
import random
import sys
import time
import urllib2

FLAGS = gflags.FLAGS

def usage(cmd):
  sys.stderr.write('Usage: %s ' % (cmd))
  return

def check_args(argv):
  try:
    argv = FLAGS(argv)
  except gflags.FlagsError:
    print FLAGS

def click_over18(response):
  br = mechanize.Browser()
  br.open(response.geturl())
  form = list(br.forms())[0]
  req = form.click(name="yes")
  return br.open(req)

def get_crawl_info():
  crawl_info = [ ]
  with open('etc/crawling.cfg') as f:
    for line in f:
      board_name, start_page, end_page = line.strip().split()
      crawl_info.append((board_name.strip(), int(start_page.strip()), int(end_page.strip())))
  return crawl_info

def crawl_ptt():
  crawl_infos = get_crawl_info()
  for crawl_info in crawl_infos:
    crawl_board(crawl_info[0], crawl_info[1], crawl_info[2])

def crawl_board(board_name, start_page, end_page):
  page_url = lambda n: 'http://www.ptt.cc/bbs/' + board_name + '/index' + str(n) + '.html'
  post_url = lambda id: 'http://www.ptt.cc/bbs/' + board_name + '/' + id + '.html'

  ## fetched files will be stored under the directory "./fetched/BOARDNAME/"
  path = os.path.join('fetched', board_name)
  try:
    os.makedirs(path)
  except:
    sys.stderr.write('Warning: "%s" already existed\n' % path)
  os.chdir(path)

  sys.stdout.write('Crawling "%s" ...\n' % board_name)
  ## determine the total number of pages for this board
  sys.stdout.write('%s\n' % page_url(1))
  sys.stdout.write('Total number of pages: %d\n' % (end_page - start_page + 1))

  ## a mapping from post_id to number of pushes
  num_pushes = dict()

  for n in xrange(start_page, end_page + 1):
    try:
      response = urllib2.urlopen(page_url(n))
      sys.stdout.write('page_url(n): %s\n' % page_url(n))
      if response.geturl().startswith('http://www.ptt.cc/ask/over18'):
        response = click_over18(response)

      page = letree.HTML(response.read())
    except:
      sys.stderr.write('Error occured while fetching %s\n' % page_url(n))
      continue

    for ele in page.findall('body/div/div/div'):
      if ele.attrib.has_key('class') and ele.attrib['class'] == 'r-ent':
        # for isnstance: 'M.1119222611.A.7A9'
        post_id = ele.xpath('div/a')[0].attrib['href'].split('/')[-1][:-5]
        try:
          num_pushes[post_id] = ele.xpath('div/span')[0].text
        except:
          num_pushes[post_id] = 0

        ## Fetch the post content
        sys.stdout.write('Fetching %s ...\n' % post_id)
        post_title = ele.xpath('div/a')[0].text
        post_author = ele.xpath('div/div')[1].text

        post_file = open(post_id, 'w')
        try:
          response = urllib2.urlopen(post_url(post_id))
          if response.geturl().startswith('http://www.ptt.cc/ask/over18'):
            response = click_over18(response)
          post = letree.HTML(response.read())
        except:
          sys.stderr.write('Error occured while fetching %s\n' % post_url(post_id))
          continue

        post_date_time = post.xpath('body/div/div/div/span')[8].text
        post_contents_ele = post.xpath('body/div/div')[2]
        post_contents = ''
        for i, t in enumerate(post_contents_ele.itertext()):
          if i > 8:
            post_contents += t

        post_file.write(post_title.encode('utf-8') + '\n')
        post_file.write(post_author.encode('utf-8') + '\n')
        post_file.write(post_date_time.encode('utf-8') + '\n')
        post_file.write(post_contents.encode('utf-8') + '\n')

        post_file.close()

        ## delay for a little while (0 - 3 sec) in fear of getting blocked
        time.sleep(3 * random.random())

  ## dump the number of pushes mapping to the file 'num_pushes_json'
  num_pushes_file = open('num_pushes_json', 'w')
  json.dump(num_pushes, num_pushes_file)

def main(argv):
  check_args(argv)
  crawl_ptt()

if __name__ == "__main__":
  main(sys.argv)

