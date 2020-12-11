from bizscraper.settings import CATEGORIES

def cleanItem(item):
  if not item: return item
  digits = ''.join(filter(lambda i: i.isdigit(), item))
  if len(digits) > 0:
    return float(digits)
  return None

def getCategory(str):
  lowerStr = str.lower()
  for key in CATEGORIES:
    for item in CATEGORIES[key]:
      if item.lower() in lowerStr:
        return key
  return 'Non-Classified'