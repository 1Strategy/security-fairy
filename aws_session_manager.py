import boto3
import logging
from botocore.exceptions import ProfileNotFound

class AWS_Session:

    def __init__(self, region_name='us-east-1', profile_name='training'):
        self.region_name    = region_name
        self.profile_name   = profile_name
        self.session        = self.__create_new_session__()

    def __create_new_session__(self):
        logging.debug("Creating a new boto3 Session object.")
        session = ''
        try:
            session = boto3.session.Session(profile_name=self.profile_name,
                                            region_name=self.region_name)
            logging.debug(session)
        except ProfileNotFound as pnf:
            session = boto3.session.Session()
        return session

    def get_session(self):
        if not self.session is None or self.session.get_credentials().__is_expired():#.__is_expired__():
            logging.debug("AWS Session expired.")
            self.session = self.__create_new_session__()
        return self.session
