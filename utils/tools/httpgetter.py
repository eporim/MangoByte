from math import perm
import re
from io import BytesIO

import aiohttp
from utils.tools.helpers import *
from utils.tools.logger import logger
from utils.tools.settings import settings
from utils.tools.cache import Cache

async def get_cloudflare_id(request):
	try:
		pattern = "Cloudflare Ray ID: <strong class=\"font-semibold\">([a-zA-Z0-9]+)</strong>"
		text = await request.text()
		match = re.search(pattern, text)
		if match:
			return match.group(1)
	except:
		return None
	return None

def raise_error(url, code, errors):
	template = errors.get(code, errors.get("default", "Http request failed with a {} error"))
	if code == 404:
		raise Http404Error(template, url)
	else:
		logger.error(f"http {code} error on: {url}")
		raise HttpError(template, url, code)

class HttpGetter:
	def __init__(self):
		self.loop = asyncio.get_event_loop()
		self.session = aiohttp.ClientSession(loop=self.loop)
		self.cache = Cache(self.loop)

	async def get(self, url: str, return_type="json", cache=False, cache_permanent=False, errors={}, headers=None):
		if cache_permanent:
			cache = True
		if cache and await self.cache.get_filename(url):
			return await self.cache.get(url, return_type)

		timer = SimpleTimer()
		async with self.session.get(url, headers=headers, timeout=60) as r:
			logger.event("httprequest", {
				"url": url,
				"status": r.status,
				"time": timer.miliseconds
			})
			if r.status == 200:
				if cache:
					await self.cache.save(url, return_type, r, permanent=cache_permanent)
					if return_type == "filename":
						return await self.cache.get_filename(url)

				if return_type == "json":
					return json.loads(await r.text(), object_pairs_hook=OrderedDict)
				elif return_type == "text":
					return await r.text()
				elif return_type == "bytes":
					return BytesIO(await r.read())
				else:
					raise ValueError(f"Invalid return type '{return_type}'")
			else:
				# text = await r.text()
				# print(f"ERROR TEXT: {text}")
				if r.status == 403:
					cloudflare_id = await get_cloudflare_id(r)
					if cloudflare_id:
						logger.error(f"http 403 cloudflare error. url: {url} RayID: {cloudflare_id}")
						# raise HttpError(f"Getting cloudflare blocked. RayID: {cloudflare_id}. Please report to developer.", url, 403)

					if "api.stratz.com" in url:
						error_message = f"Http 403 Auth error on STRATZ request:\n<{url}>\n"
						if cloudflare_id:
							error_message += f"\nGotta complain in discord using this cloudflare ID: {cloudflare_id}"
						else:
							error_message += f"\nAPI token probably expired. Gotta get new one: <https://stratz.com/api>"
						try:
							text = await r.text()
							if text:
								error_message += f"\n```{text}```"
						except:
							pass
						user_message = "Got a STRATZ auth error. I've notified the bot developer of the issue. Try again in a day or so."
						raise DeveloperNotifError(user_message, error_message)



				raise_error(url, r.status, errors)

	async def post(self, url, return_type="json", errors={}, body={}, headers={}):
		timer = SimpleTimer()
		async with self.session.post(url, json=body, headers=headers) as r:
			logger.event("httprequest", {
				"url": url,
				"status": r.status,
				"time": timer.miliseconds,
				"method": "POST"
			})
			if r.status == 200:
				if return_type == "json":
					return json.loads(await r.text(), object_pairs_hook=OrderedDict)
				elif return_type == "text":
					return await r.text()
				elif return_type == "bytes":
					return BytesIO(await r.read())
				else:
					raise ValueError(f"Invalid return type '{return_type}'")
			else:
				raise_error(url, r.status, errors)

httpgetter = HttpGetter()


