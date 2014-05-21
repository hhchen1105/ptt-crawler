#!/usr/bin/env python

'''
Modified from bruce3557/PTT-Crawler: https://github.com/bruce3557/PTT-Crawler
'''

# Hung-Hsuan Chen <hhchen@psu.edu>
# Creation Date : 05-21-2014
# Last Modified: Wed 21 May 2014 05:52:18 AM EDT

import bs4
import gflags
import json
import mechanize
import os
import sys
import time
import urllib2

FLAGS = gflags.FLAGS
gflags.DEFINE_string('board_name', '', '')
gflags.DEFINE_integer('start_page', 0, '')
gflags.DEFINE_integer('end_page', 0, '')

def usage(cmd):
  sys.stderr.write('Usage: %s --board_name="Gossiping" '
      '--start_page=1 --end_page=5\n' % (cmd))
  return

def check_args(argv):
  try:
    argv = FLAGS(argv)
  except gflags.FlagsError:
    print FLAGS

  if FLAGS.board_name == '':
    usage(argv[0])
    raise Exception('flag --board_name cannot be empty')

  if FLAGS.start_page <= 0:
    usage(argv[0])
    raise Exception('flag --start_page must be a positive integer')

  if FLAGS.end_page <= 0:
    usage(argv[0])
    raise Exception('flag --end_page must be a positive integer')

def click_over18(response):
  br = mechanize.Browser()
  br.open(response.geturl())
  form = list(br.forms())[0]
  req = form.click(name="yes")
  return br.open(req)

def crawl_ptt():
  page_url = lambda n: 'http://www.ptt.cc/bbs/' + FLAGS.board_name + '/index' + str(n) + '.html'
  post_url = lambda id: 'http://www.ptt.cc/bbs/' + FLAGS.board_name + '/' + id + '.html'

  ## fetched files will be stored under the directory "./fetched/BOARDNAME/"
  path = os.path.join('fetched', FLAGS.board_name)
  try:
    os.makedirs(path)
  except:
    sys.stderr.write('Warning: "%s" already existed\n' % path)
  os.chdir(path)

  sys.stdout.write('Crawling "%s" ...\n' % FLAGS.board_name)
  ## determine the total number of pages for this board
  sys.stdout.write('%s' % page_url(1))
  page = bs4.BeautifulSoup(urllib2.urlopen(page_url(1)).read())
  sys.stdout.write('Total number of pages: %d\n' % (FLAGS.end_page - FLAGS.start_page + 1))

  ## a mapping from post_id to number of pushes
  num_pushes = dict()

  for n in xrange(FLAGS.start_page, FLAGS.end_page + 1):
    try:
      response = urllib2.urlopen(page_url(n))
      sys.stdout.write('page_url(n): %s' % page_url(n))
      if response.geturl().startswith('http://www.ptt.cc/ask/over18'):
        response = click_over18(response)

      page = bs4.BeautifulSoup(response.read())
    except:
      sys.stderr.write('Error occured while fetching %s\n' % page_url(n))
      continue
    for tr in page.find_all('div', 'r-ent'):
      ## For instance: "M.1368632629.A.AF7"
      post_id = tr.contents[5].contents[1].get('href').split('/')[-1][:-5]
      ## Record the number of pushes, which is an integer from -100 to 100
      try:
        num_pushes[post_id] = tr.contents[1].contents[0].contents[0]
      except:
        num_pushes[post_id] = 0
      ## Fetch the post content
      sys.stdout.write('Fetching %s ...\n' % post_id)
      post_file = open(post_id, 'w')

      try:
        response = urllib2.urlopen(post_url(post_id))
        if response.geturl().startswith('http://www.ptt.cc/ask/over18'):
          response = click_over18(response)
        post = bs4.BeautifulSoup(response.read())
      except:
        sys.stderr.write('Error occured while fetching %s\n' % post_url(post_id))
        continue

      if post.find(id='main-content') is None:
        print 'iiiii'
        continue
      for content in post.find(id='main-content').contents:
        ## u'\u25c6' is the starting character in the 'source ip line',
        ## which for instance looks like "u'\u25c6' From: 111.253.164.108"
        if type(content) is bs4.element.NavigableString and content[0] != u'\u25c6':
          post_file.write(content.encode('utf-8'))
      for push in post.find_all('div', 'push'):
        post_file.write(push.contents[1].contents[0].encode('utf-8') + push.contents[2].contents[0].encode('utf-8'))

      post_file.close()

      ## delay for a little while in fear of getting blocked
      time.sleep(0.1)

  ## dump the number of pushes mapping to the file 'num_pushes_json'
  num_pushes_file = open('num_pushes_json', 'w')
  json.dump(num_pushes, num_pushes_file)

def main(argv):
  check_args(argv)
  crawl_ptt()

if __name__ == "__main__":
  main(sys.argv)

