#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Amazon Feed

from ..mws import *

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)


class AmazonFeed(models.Model):
    """Amazon Feed"""
    _name = 'amazon.feed'
    _description = 'Amazon Feed Manage'
    name = fields.Char('Feed Id')
    amazon_profile = fields.Many2one('amazon')
    feed_type = fields.Char('Feed Type')
    submitted_date = fields.Datetime('Submitted Date')
    feed_xml = fields.Text('Feed XML')
    status = fields.Char(index=True)
    message_processed = fields.Integer()
    message_successful = fields.Integer()
    message_error = fields.Integer()
    message_warning = fields.Integer()
    error_info = fields.Text()

    @api.multi
    def check_feed(self):
        """检查FEED提交结果"""
        for feed in self:
            mws_model = mws.Feeds(feed.amazon_profile.access_key, feed.amazon_profile.secret_key,
                                  feed.amazon_profile.account_id,
                                  feed.amazon_profile.region)
            respon = mws_model.get_feed_submission_result(feed.name)
            report = respon.parsed
            if report['ProcessingReport']['StatusCode']['value'] == 'Complete':
                error_info = None
                if 'Result' in report['ProcessingReport'].keys():
                    for i in report['ProcessingReport']['Result']:
                        error_info += i['ResultCode'], i['ResultDescription']
                feed.update({
                    'status': report['ProcessingReport']['StatusCode']['value'],
                    'message_processed': report['ProcessingReport']['ProcessingSummary']['MessagesProcessed']['value'],
                    'message_successful': report['ProcessingReport']['ProcessingSummary']['MessagesSuccessful']['value'],
                    'message_error': report['ProcessingReport']['ProcessingSummary']['MessagesWithError']['value'],
                    'message_warning': report['ProcessingReport']['ProcessingSummary']['MessagesWithWarning']['value'],
                    'error_info': error_info
                })

    @api.model
    def auto_check_feed(self):
        """查询FEED执行结果定时任务"""
        feeds = self.search([('status', '!=', 'Complete')])
        for feed in feeds:
            mws_model = mws.Feeds(feed.amazon_profile.access_key, feed.amazon_profile.secret_key,
                                  feed.amazon_profile.account_id,
                                  feed.amazon_profile.region)
            respon = mws_model.get_feed_submission_result(feed.name)
            report = respon.parsed
            if report['ProcessingReport']['StatusCode']['value'] == 'Complete':
                error_info = None
                if 'Result' in report['ProcessingReport'].keys():
                    for i in report['ProcessingReport']['Result']:
                        error_info += i['ResultCode'], i['ResultDescription']

                feed.update({
                    'status': report['ProcessingReport']['StatusCode']['value'],
                    'message_processed': report['ProcessingReport']['ProcessingSummary']['MessagesProcessed']['value'],
                    'message_successful': report['ProcessingReport']['ProcessingSummary']['MessagesSuccessful'][
                        'value'],
                    'message_error': report['ProcessingReport']['ProcessingSummary']['MessagesWithError']['value'],
                    'message_warning': report['ProcessingReport']['ProcessingSummary']['MessagesWithWarning']['value'],
                    'error_info': error_info
                })


