class BaseNode():
    """Ancestor of the various node types.

    Stores common functionality of child classes, but should not be
    instantiated.
    """

    def __init__(self, **kwargs):
        for arg, value in kwargs.items():
            setattr(self, arg, value)

    def __repr__(self):
        user = '{0}(id={1})'.format(self.user.__class__, self.user.id)
        clean_dict = self.__dict__.copy()
        clean_dict['user'] = user
        return '{0}({1})'.format(self.__class__, clean_dict)

    @classmethod
    def from_response(cls, user, response):
        """Construct a BaseNode from a response dict."""
        args = {
          'user': user,
          'type': response.get('type'),
          'id': response.get('_id'),
          'is_active': response.get('is_active'),
          'permission': response.get('allowed'),
          'nickname': response['info'].get('nickname'),
          'name_on_account': response['info'].get('name_on_account'),
          'bank_long_name': response['info'].get('bank_long_name'),
          'bank_name': response['info'].get('bank_name'),
          'account_type': response['info'].get('type'),
          'account_class': response['info'].get('class'),
          'account_number': response['info'].get('account_num'),
          'routing_number': response['info'].get('routing_num'),
          'account_id': response['info'].get('account_id'),
          'address': response['info'].get('address'),
          'swift': response['info'].get('swift'),
          'ifsc': response['info'].get('ifsc')
        }

        if response['info'].get('correspondent_info'):
            info = response['info']['correspondent_info']
            args['correspondent_swift'] = info.get('swift')
            args['correspondent_bank_name'] = info.get('bank_name')
            args['correspondent_routing_number'] = info.get('routing_num')
            args['correspondent_address'] = info.get('address')

        if response['info'].get('match_info'):
            match_info = response['info']['match_info']
            args['email_match'] = match_info.get('email_match')
            args['name_match'] = match_info.get('name_match')
            args['phonenumber_match'] = match_info.get('phonenumber_match')

        if response['info'].get('balance'):
            info = response['info']['balance']
            args['balance'] = info.get('amount')
            args['currency'] = info.get('currency')

        if response.get('extra'):
            info = response['extra']
            args['supp_id'] = info.get('supp_id')
            args['gateway_restricted'] = info.get('gateway_restricted')

        return cls(**args)

    @classmethod
    def multiple_from_response(cls, user, response):
        """Construct multiple BaseNodes from a response dict."""
        nodes = [cls.from_response(user, node_data)
                 for node_data in response]
        return nodes

    @classmethod
    def payload_for_create(cls, type, **kwargs):
        """Construct the 'add node' payload from property values."""
        payload = {
            'type': type,
            'info': {}
        }

        options = ['swift', 'name_on_account', 'bank_name', 'address', 'ifsc',
                   'nickname', 'bank_name']
        for option in options:
            if option in kwargs:
                payload['info'][option] = kwargs[option]

        # the rest are done individually since they are custom renamed
        correspondent_info = {}
        if 'correspondent_routing_number' in kwargs:
            correspondent_info['routing_num'] = kwargs['correspondent_routing_number']
        if 'correspondent_bank_name' in kwargs:
            correspondent_info['bank_name'] = kwargs['correspondent_bank_name']
        if 'correspondent_address' in kwargs:
            correspondent_info['address'] = kwargs['correspondent_address']
        if 'correspondent_swift' in kwargs:
            correspondent_info['swift'] = kwargs['correspondent_swift']
        if correspondent_info:
            payload['info']['correspondent_info'] = correspondent_info
        if 'account_number' in kwargs:
            payload['info']['account_num'] = kwargs['account_number']
        if 'routing_number' in kwargs:
            payload['info']['routing_num'] = kwargs['routing_number']
        if 'account_type' in kwargs:
            payload['info']['type'] = kwargs['account_type']
        if 'account_class' in kwargs:
            payload['info']['class'] = kwargs['account_class']
        if 'username' in kwargs:
            payload['info']['bank_id'] = kwargs['username']
        if 'password' in kwargs:
            payload['info']['bank_pw'] = kwargs['password']

        balance_options = ['currency']
        balance = {}
        for option in balance_options:
            if option in kwargs:
                balance[option] = kwargs[option]
        if balance:
            payload['info']['balance'] = balance

        extra_options = ['supp_id', 'gateway_restricted']
        extra = {}
        for option in extra_options:
            if option in kwargs:
                extra[option] = kwargs[option]
        if extra:
            payload['extra'] = extra
        return payload

    @classmethod
    def create(cls, user=None, nickname=None, **kwargs):
        """Create a node record in API and corresponding BaseNode instance.

        See subclasses for more information about type-specific args.
        """
        payload = cls.payload_for_create(nickname, **kwargs)
        response = user.client.nodes.create(user.id, payload)
        return cls.from_response(user, response['nodes'][0])

    def deactivate(self):
        """Deactivate and deindex the node.

        The node will not appear in results lists and will not be available to
        create new transactions. This does not cancel transactions already
        underway.

        Returns:
            BaseNode: a BaseNode instance corresponding to the record
        """
        response = self.user.client.nodes.delete(self.user.id, self.id)
        if '_id' in response:
            # api v3.1.1
            return self.__class__.from_response(self, response)
        else:
            # api v3.1.0
            return None
