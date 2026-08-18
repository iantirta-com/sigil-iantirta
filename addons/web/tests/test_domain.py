# -*- coding: utf-8 -*-

import json

from sigil.addons.base.tests.common import HttpCaseWithUserDemo
from sigil.tests import tagged
from sigil.tools import mute_logger


@tagged('post_install', '-at_install')
class DomainTest(HttpCaseWithUserDemo):

    def test_domain_validate(self):
        self.authenticate("demo", "demo")

        with mute_logger('sigil.http'):
            resp = self.url_open(
                '/web/domain/validate',
                headers={'Content-Type': 'application/json'},
                data=json.dumps({'params': {'model':'i', 'domain':[]}}),
            )
        self.assertEqual(resp.json()['error']['data']['message'], "Invalid model: i")

        resp = self.url_open(
            '/web/domain/validate',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'params': {'model':'res.users', 'domain':[]}}),
        )
        self.assertEqual(resp.json()['result'], True)

        resp = self.url_open(
            '/web/domain/validate',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'params': {'model':'res.users', 'domain':[('name', 'ilike', 'ad')]}}),
        )
        self.assertEqual(resp.json()['result'], True)

        resp = self.url_open(
            '/web/domain/validate',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'params': {'model':'res.users', 'domain':[('hop')]}}),
        )
        self.assertEqual(resp.json()['result'], False)
