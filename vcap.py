import os, json
from urllib.parse import urlparse
from cloudant.client import Cloudant
import redis

class VCap(object):
  def __init__(self, jsonFileName):
    if 'VCAP_SERVICES' in os.environ:
      self.vcap = json.loads(os.getenv('VCAP_SERVICES'))
    else:
      f = open(jsonFileName)
      self.vcap = json.loads(f.read())
      f.close()
  
  def cloudantConfig(self):
    if 'cloudantNoSQLDB' not in self.vcap:
      return None

    creds = self.vcap['cloudantNoSQLDB'][0]['credentials']
    user = creds['username']
    password = creds['password']
    url = 'https://' + creds['host']
    return (user, password, url)

  def redisConfig(self):
    if 'compose-for-redis' not in self.vcap:
      return None
    return self.vcap['compose-for-redis'][0]['credentials']['uri']
  
  def initRedis(self):
    compose_redis_url = self.redisConfig()
    if not compose_redis_url:
      return None
    
    ssl_wanted=compose_redis_url.startswith("rediss:")
    parsed = urlparse(compose_redis_url)
    ssl_wanted=compose_redis_url.startswith("rediss:")
    return redis.StrictRedis(
              host=parsed.hostname,
              port=parsed.port,
              password=parsed.password,
              ssl=ssl_wanted,
              decode_responses=True)
  
  def initCloudant(self):
    config = self.cloudantConfig()
    if not config:
      return None

    (user, password, url) = config
    return Cloudant(user, password, url=url, connect=True)
