#!/usr/bin/env python3
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import io
import os.path
import sys
import urllib.parse

import click
import progressbar
import requests
from lxml import html


def fmt_size(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def download_media(base_dir, url, force=False):
    ## TODO: Check URL sanity
    r = requests.get(url)
    tree = html.fromstring(r.text)

    media_url = tree.xpath('//a[@style="font-size: 16px; font-weight:bold;"]')[0].get('href')

    (_, _, song_path) = media_url.partition('/Music/')
    rel_path = urllib.parse.unquote(song_path)
    local_path = os.path.join(base_dir, rel_path)

    try:
        os.makedirs(os.path.join(base_dir, os.path.dirname(rel_path)))
    except FileExistsError:
        pass

    print("Downloading... '{}'".format(rel_path), end='', flush=True)

    # Refer must be set to the requesting url
    headers={'Referer': url}


    response = requests.head(media_url, headers=headers)
    print(response.encoding)
    size = int(response.headers['content-length'])

    try:
        local_size = os.path.getsize(local_path)
        if local_size == size and not force:
            print(" -- appears to be aleady downloaded. Skipping.")
            return
    except FileNotFoundError:
        pass

    print(" ({})".format(fmt_size(size)))
    pbar_widgets = [
        progressbar.Percentage(),
        progressbar.Bar(),
        progressbar.ETA()
    ]

    response = requests.get(media_url, headers=headers, stream=True)
    with open(local_path, 'wb') as f:
        dl_size = 0
        pbar = progressbar.ProgressBar(widgets=pbar_widgets, maxval=size)
        pbar.start()
        for chunk in response.iter_content(chunk_size=1024):
            if not chunk:
                continue
            f.write(chunk)
            f.flush()
            dl_size += len(chunk)
            pbar.update(dl_size)
        pbar.finish()

@click.command()
@click.option('-d', '--dir', type=click.Path(file_okay=False),
              default=os.getcwd(), help="Destination directory")
@click.argument('url')
def main(url, dir):
    page = requests.get(url)

    tree = html.fromstring(page.text)
    tree.make_links_absolute('http://www.emuparadise.me')

    download_links = tree.xpath('//td/a[//*[contains(text(), "Download")]]')
    for link in download_links:
        song_url = link.get('href')
        download_media(dir, song_url)


if __name__ == '__main__':
    main()
