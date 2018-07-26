import ast
import falcon
import json
import os
import redis
import uuid

from datetime import datetime
from .routes import paths, version


class Endpoints(object):

    def on_get(self, req, resp):
        endpoints = []
        for path in paths():
            endpoints.append(version()+path)

        resp.body = json.dumps(endpoints)
        resp.content_type = falcon.MEDIA_TEXT
        resp.status = falcon.HTTP_200


class Info(object):

    def on_get(self, req, resp):
        resp.body = json.dumps({'version': 'v0.1.0'})
        resp.content_type = falcon.MEDIA_TEXT
        resp.status = falcon.HTTP_200


class NetworkFull(object):

    def connect_redis(self):
        self.r = None
        try:
            if 'POSEIDON_TRAVIS' in os.environ:
                self.r = redis.StrictRedis(host='localhost',
                                           port=6379,
                                           db=0,
                                           decode_responses=True)
            else:
                self.r = redis.StrictRedis(host='redis',
                                           port=6379,
                                           db=0,
                                           decode_responses=True)
        except Exception as e:  # pragma: no cover
            return (False, 'unable to connect to redis because: ' + str(e))
        return (True, 'connected')

    def get_dataset(self):
        dataset = []
        status = self.connect_redis()
        if status[0] and self.r:
            try:
                ip_addresses = self.r.smembers('ip_addresses')
                for ip_address in ip_addresses:
                    node = {}
                    node['ip'] = ip_address
                    node['mac'] = 0
                    node['segment'] = 0
                    node['port'] = 0
                    node['tenant'] = 0
                    node['record_source'] = 'Poseidon'
                    node['role'] = 'Unknown'
                    node['os'] = 'Unknown'
                    node['behavior'] = 0
                    node['hash'] = '0'
                    node['state'] = 'UNDEFINED'
                    node['active'] = 0
                    try:
                        ip_info = self.r.hgetall(ip_address)
                        if 'poseidon_hash' in ip_info:
                            node['hash'] = ip_info['poseidon_hash']
                            try:
                                poseidon_info = self.r.hgetall(ip_info['poseidon_hash'])
                                if 'endpoint_data' in poseidon_info:
                                    endpoint_data = ast.literal_eval(poseidon_info['endpoint_data'])
                                    node['mac'] = endpoint_data['mac']
                                    node['segment'] = endpoint_data['segment']
                                    node['port'] = endpoint_data['port']
                                    node['tenant'] = endpoint_data['tenant']
                                    node['active'] = endpoint_data['active']
                                if 'state' in poseidon_info:
                                    node['state'] = poseidon_info['state']
                            except Exception as e:  # pragma: no cover
                                pass
                        if 'timestamps' in ip_info:
                            try:
                                timestamps = ast.literal_eval(ip_info['timestamps'])
                                ml_info = self.r.hgetall(ip_address+'_'+str(timestamps[-1]))
                                if 'labels' in ml_info:
                                    labels = ast.literal_eval(ml_info['labels'])
                                    node['role'] = labels[0]
                            except Exception as e:  # pragma: no cover
                                pass
                        if 'short_os' in ip_info:
                            short_os = ip_info['short_os']
                            node['os'] = short_os
                    except Exception as e:  # pragma: no cover
                        pass
                    dataset.append(node)
            except Exception as e:  # pragma: no cover
                pass
        return dataset

    def on_get(self, req, resp):
        network = {}
        dataset = self.get_dataset()
        network['dataset'] = dataset

        resp.body = json.dumps(network, indent=2)
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200

class Network(object):

    def connect_redis(self):
        self.r = None
        try:
            if 'POSEIDON_TRAVIS' in os.environ:
                self.r = redis.StrictRedis(host='localhost',
                                           port=6379,
                                           db=0,
                                           decode_responses=True)
            else:
                self.r = redis.StrictRedis(host='redis',
                                           port=6379,
                                           db=0,
                                           decode_responses=True)
        except Exception as e:  # pragma: no cover
            return (False, 'unable to connect to redis because: ' + str(e))
        return (True, 'connected')

    def get_dataset(self):
        dataset = []
        status = self.connect_redis()
        if status[0] and self.r:
            try:
                ip_addresses = self.r.smembers('ip_addresses')
                for ip_address in ip_addresses:
                    node = {}
                    # TODO lock in the uid
                    node['uid'] = str(uuid.uuid4())
                    node['IP'] = ip_address
                    # cheating for now
                    if ':' in ip_address:
                        node['subnet'] = ':'.join(ip_address.split(':')[0:4])+"::0/64"
                    else:
                        node['subnet'] = '.'.join(ip_address.split('.')[:-1])+".0/24"
                    # setting to unknown for now
                    node['rDNS_host'] = 'Unknown'
                    # set as unknown until it's set below
                    node['mac'] = 'Unknown'
                    node['record'] = {}
                    node['role'] = {}
                    node['role']['role'] = 'Unknown'
                    node['os'] = {}
                    node['os']['os'] = 'Unknown'
                    try:
                        short_os = None
                        endpoint_data = {}
                        labels = []
                        confidences = []
                        ip_info = self.r.hgetall(ip_address)

                        if 'poseidon_hash' in ip_info:
                            try:
                                poseidon_info = self.r.hgetall(ip_info['poseidon_hash'])
                                if 'endpoint_data' in poseidon_info:
                                    endpoint_data = ast.literal_eval(poseidon_info['endpoint_data'])
                                    node['mac'] = endpoint_data['mac']
                            except Exception as e:  # pragma: no cover
                                pass
                        if 'timestamps' in ip_info:
                            try:
                                timestamps = ast.literal_eval(ip_info['timestamps'])
                                node['record']['source'] = 'poseidon'
                                node['record']['timestamp'] = str(datetime.fromtimestamp(float(timestamps[-1])))
                                ml_info = self.r.hgetall(ip_address+'_'+str(timestamps[-1]))
                                if 'labels' in ml_info:
                                    labels = ast.literal_eval(ml_info['labels'])
                                    node['role']['role'] = labels[0]
                                if 'confidences' in ml_info:
                                    confidences = ast.literal_eval(ml_info['confidences'])
                                    node['role']['confidence'] = int(confidences[0]*100)
                            except Exception as e:  # pragma: no cover
                                pass
                        if 'short_os' in ip_info:
                            short_os = ip_info['short_os']
                            node['os']['os'] = short_os
                    except Exception as e:  # pragma: no cover
                        pass
                    dataset.append(node)
            except Exception as e:  # pragma: no cover
                pass

        return dataset

    def get_configuration(self):
        configuration = {}
        return configuration

    def on_get(self, req, resp):
        network = {}
        dataset = self.get_dataset()
        configuration = self.get_configuration()

        network["dataset"] = dataset
        network["configuration"] = configuration
        resp.body = json.dumps(network, indent=2)
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200
