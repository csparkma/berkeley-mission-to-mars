from splinter import Browser
from bs4 import BeautifulSoup as bsoup
import pandas as pd
import datetime as dt

def scrape_all():
    # Initiate headless driver for deployment
   browser = Browser("chrome", executable_path="chromedriver", headless=True)
   news_title, news_paragraph = mars_news(browser)

   # Run all scraping functions and store results in dictionary
   data = {
          "news_title": news_title,
          "news_paragraph": news_paragraph,
          "featured_image": featured_image(browser),
          "facts": mars_facts(),
          "hemisphere_images": high_res_images(browser),
          "last_modified": dt.datetime.now()
    }
   # Stop webdriver and return data
   browser.quit()
   return data

def get_html(browser):
    """Returns html from BeautifulSoup html parser based on web object passsed in."""
    return bsoup(browser.html, 'html.parser')

def mars_news(browser):
    """Scrape Mars News"""

    # Visit the mars nasa news site
    url = 'https://mars.nasa.gov/news/'
    browser.visit(url)

    # Optional delay for loading the page
    browser.is_element_present_by_css("ul.item_list li.slide", wait_time=5)

    # Convert the browser html to a soup object and then quit the browser
    news_soup = get_html(browser)

    try:
        slide_elem = news_soup.select_one('ul.item_list li.slide')

        # Use t she parent element to find the first `a` tag and save it as `news_title`
        news_title = slide_elem.find("div", class_='content_title').get_text()

        # Use the parent element to find the paragraph text
        news_p = slide_elem.find('div', class_="article_teaser_body").get_text()
    except AttributeError:
        return None, None

    return news_title, news_p

def featured_image(browser):
    """Scrape Featured Images"""

    # Visit URL
    url = 'https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars'
    browser.visit(url)

    # Find and click the full image button
    full_image_elem = browser.find_by_id('full_image')
    full_image_elem.click()

    # Find the more info button and click that
    browser.is_element_present_by_text('more info', wait_time=1)
    more_info_elem = browser.links.find_by_partial_text('more info')
    more_info_elem.click()

    # Parse the resulting html with soup
    img_soup = get_html(browser)

    try:
        # Find the relative image url
        img_url_rel = img_soup.select_one('figure.lede a img').get("src")
    except AttributeError:
        return None

    # Use the base URL to create an absolute URL
    img_url = f'https://www.jpl.nasa.gov{img_url_rel}'

    return img_url

def mars_facts():
    try:
        # use 'read_html' to scrape the facts table into a dataframe.
        df = pd.read_html('http://space-facts.com/mars/')[0]
    except BaseException:
        return None

    # Assign columns and set index of dataframe
    df.columns=['description', 'value']
    df.set_index('description', inplace=True)

    # Convert dataframe into HTML format, add bootstrap
    return df.to_html()

def high_res_images(browser):
    images = []
    """Scrape Images"""

    # Visit URL
    base_url = 'https://astrogeology.usgs.gov/'
    start_url = '/search/results?q=hemisphere+enhanced&k1=target&v1=Mars'

    # Visit web page and get HTML
    browser.visit(base_url + start_url)
    soup = get_html(browser)

    # Find main_urls for hemispheres
    main_urls = soup.find_all('a', class_='itemLink product-item')

    # Parse through main_urls to find links
    for link in main_urls:
        # Due to links on image icons as well, we only grab link with header
        is_link_header = link.find('h3')

        # Only links with header will have a title
        if is_link_header:
            title = is_link_header.text
            hemisphere_url = link['href']
            # Now that we've found the right link, visit hemisphere page and get HTML to find image link
            browser.visit(base_url + hemisphere_url)
            soup = get_html(browser)

            # Find image reference and if found, append title and url to full high-resolution image to image list
            hemisphere_image_ref = soup.find('img', class_='wide-image')
            if hemisphere_image_ref:
                images.append(dict({
                    'title': title
                    , 'img_url': base_url + hemisphere_image_ref['src']
                }))
    return images

if __name__ == "__main__":
    # If running as script, print scraped data
    print(scrape_all())
