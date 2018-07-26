#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Copyright (c) 2016-2017 In-Q-Tel, Inc, All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
'''
Created on 14 July 2016
@author: dgrossman
'''
from poseidon.baseClasses.Logger_Base import Logger
from poseidon.baseClasses.Rock_Bottom import Rock_Bottom

module_logger = Logger


class Monitor_Helper_Base(Rock_Bottom):  # pragma: no cover
    '''base class for the helper objets'''

    def __init__(self):
        super(Monitor_Helper_Base, self).__init__()

    def set_owner(self, owner):
        '''set the parent class

        Args:
            owner: class to be contacted to use other methods
        '''

        if owner.logger is not None:
            self.logger = owner.logger
        else:
            self.logger = module_logger.logger

        self.logger.debug('set_owner = {0}'.format(owner.mod_name))
        self.owner = owner
        if self.owner.mod_name is not None:
            self.config_section_name = self.owner .mod_name + ':' + self.mod_name
        else:
            self.config_section_name = 'None:' + self.mod_name

    def configure(self):
        '''get, parse, store configuration internally as dict'''
        ostr = '{0} {1}'.format(self.mod_name, 'configure()')
        self.logger.info(ostr)
        # local valid
        if not self.owner:
            ostr = '{0} {1}'.format(self.mod_name, 'ownerNull')
            self.logger.error(ostr)
            return
        # monitor valid
        if not self.owner.owner:
            ostr = '{0} {1}'.format(self.mod_name, 'monitorNull')
            self.logger.error(ostr)
            return
        self.mod_configuration = dict()
        conf = self.owner.owner.Config.get_endpoint('Handle_SectionConfig')
        #ostr = '********** conf:{0}'.format(conf)
        #print(ostr)
        if conf is not None:
            for item in conf.direct_get(self.config_section_name):
                #ostr = '********** item:{0}'.format(item)
                #self.logger.debug(ostr)
                k, v = item
                self.mod_configuration[k] = v
                #ostr = 'config:{0}:{1}'.format(
                #    self.config_section_name, self.mod_configuration)
                #self.logger.debug(ostr)
            self.configured = True

    def first_run(self):
        '''do special setup after configure'''
