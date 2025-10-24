import json
import urllib.parse
import aiohttp

quoteurl = urllib.parse.quote


#import locale

class Jeedom():
	def __init__(self, adrss, apiKey):
		self.adrss = adrss + '/core/api/jeeApi.php?request='
		self.apiKey = apiKey
		self.eqLogic = self._eqLogic(self)
		self.cmd = self._cmd(self)


	async def ping(self):
		_params = {"method":"ping"}
		return await self.callJeedom(_params)

	async def version(self):
		_params = {"method":"version"}
		return await self.callJeedom(_params)

	async def isOk(self):
		_params = {"method":"jeedom::isOk"}
		return await self.callJeedom(_params)

	class _eqLogic:
		def __init__(self, parent):
			self.jeedom = parent

		async def byType(self, type=None):
			_params = {"method":"eqLogic::byType"}
			_params['params'] = {}
			_params['params']['type'] = type
			return await self.jeedom.callJeedom(_params)

		async def fullById(self, id=None):
			_params = {"method":"eqLogic::fullById"}
			_params['params'] = {}
			_params['params']['id'] = id
			return await self.jeedom.callJeedom(_params)

	class _cmd:
		def __init__(self, parent):
			self.jeedom = parent

		async def execCmd(self, id=None, options=None):
			_params = {"method":"cmd::execCmd"}
			_params['params'] = {}
			_params['params']['id'] = id
			_params['params']['options'] = options
			return await self.jeedom.callJeedom(_params)


	async def callJeedom(self, _params=''):
		if not 'params' in _params:
			_params['params'] = {}
		_params['params']['apikey'] = self.apiKey
		_params['jsonrpc'] = "2.0"
		data = json.dumps(_params)
		url  = self.adrss + quoteurl(data)

		async with aiohttp.ClientSession() as session:
			try:
				async with session.post(url, data=data) as response:
					result = await response.json()
					if 'error' in result: return result
					return result['result']

			except aiohttp.ClientResponseError as e:
				return {"error":e}