import logging

class AWS_Session:

    def __init__(region_name='us-east-1', profile_name='training'):
        self.session        = self.__create_new_session__()
        self.region_name    = region_name
        self.profile_name   = profile_name

    def __create_new_session__():
        logging.debug("Creating a new boto3 Session object.")
        try:
            self.session = boto3.session.Session(   profile_name=self.profile_name,
                                                    region_name=self.region_name)
        except ProfileNotFound as pnf:
            self.session = boto3.session.Session()

    def get_session():
        if self.session.get_credentials().__is_expired__():
            logging.debug("AWS Session expired.")
            self.__create_new_session__()
            return self.session
        return self.session
