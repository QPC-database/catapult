# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Polls the sheriff_config service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from dashboard.common import defaults


class InternalServerError(Exception):
  """An error indicating that something unexpected happens."""
  pass


def GetSheriffConfigClient():
  """Get a cached SheriffConfigClient instance.
  Most code should use this rather than constructing a SheriffConfigClient
  directly.
  """
  # pylint: disable=protected-access
  if not hasattr(GetSheriffConfigClient, '_client'):
    GetSheriffConfigClient._client = SheriffConfigClient()
  return GetSheriffConfigClient._client


class SheriffConfigClient(object):
  """Wrapping of sheriff-config HTTP API."""

  _Subscription = None

  def __init__(self):
    """Make the Cloud Endpoints request from this handler."""
    # Defer as many imports as possible until here, to ensure AppEngine
    # workarounds for protobuf import paths are fully installed.
    self._InitSession()
    from dashboard.common.utils import GetEmail
    from dashboard.models.subscription import Subscription, AnomalyConfig
    from google.protobuf import json_format
    from dashboard import sheriff_config_pb2
    self._GetEmail = GetEmail  # pylint: disable=invalid-name
    SheriffConfigClient._Subscription = Subscription
    SheriffConfigClient._AnomalyConfig = AnomalyConfig
    self._json_format = json_format
    self._sheriff_config_pb2 = sheriff_config_pb2

  def _InitSession(self):
    import google.auth
    from google.auth import jwt
    from google.auth.transport.requests import AuthorizedSession
    credentials, _ = google.auth.default(
        scopes=['https://www.googleapis.com/auth/userinfo.email'])
    jwt_credentials = jwt.Credentials.from_signing_credentials(
        credentials, 'sheriff-config-dot-chromeperf.appspot.com')
    self._session = AuthorizedSession(jwt_credentials)

  @staticmethod
  def _ParseSubscription(revision, subscription):
    anomaly_configs = [
        SheriffConfigClient._AnomalyConfig(
            max_window_size=a.max_window_size or defaults.MAX_WINDOW_SIZE,
            min_segment_size=a.min_segment_size or defaults.MIN_SEGMENT_SIZE,
            min_absolute_change=a.min_absolute_change
            or defaults.MIN_ABSOLUTE_CHANGE,
            min_relative_change=a.min_relative_change
            or defaults.MIN_RELATIVE_CHANGE,
            min_steppiness=a.min_steppiness or defaults.MIN_STEPPINESS,
            multiple_of_std_dev=a.multiple_of_std_dev
            or defaults.MULTIPLE_OF_STD_DEV,
        ) for a in subscription.anomaly_configs
    ]
    return SheriffConfigClient._Subscription(
        revision=revision,
        name=subscription.name,
        rotation_url=subscription.rotation_url,
        notification_email=subscription.notification_email,
        monorail_project_id=subscription.monorail_project_id,
        bug_labels=list(subscription.bug_labels),
        bug_components=list(subscription.bug_components),
        bug_cc_emails=list(subscription.bug_cc_emails),
        visibility=subscription.visibility,
        auto_triage_enable=subscription.auto_triage.enable,
        auto_bisect_enable=subscription.auto_bisection.enable,
        anomaly_configs=anomaly_configs,
    )

  def Match(self, path, check=False):
    response = self._session.post(
        'https://sheriff-config-dot-chromeperf.appspot.com/subscriptions/match',
        json={'path': path})
    if response.status_code == 404:  # If no subscription matched
      return [], None
    if not response.ok:
      err_msg = '%r\n%s' % (response, response.text)
      if check:
        raise InternalServerError(err_msg)
      return None, err_msg
    match_resp = self._json_format.Parse(
        response.text, self._sheriff_config_pb2.MatchResponse())
    return [
        self._ParseSubscription(s.revision, s.subscription)
        for s in match_resp.subscriptions
    ], None

  def List(self, check=False):
    response = self._session.post(
        'https://sheriff-config-dot-chromeperf.appspot.com/subscriptions/list',
        json={'identity_email': self._GetEmail()})
    if not response.ok:
      err_msg = '%r\n%s' % (response, response.text)
      if check:
        raise InternalServerError(err_msg)
      return None, err_msg
    list_resp = self._json_format.Parse(response.text,
                                        self._sheriff_config_pb2.ListResponse())
    return [
        self._ParseSubscription(s.revision, s.subscription)
        for s in list_resp.subscriptions
    ], None

  def Update(self, check=False):
    response = self._session.get(
        'https://sheriff-config-dot-chromeperf.appspot.com/configs/update')
    if response.ok:
      return True, None
    err_msg = '%r\n%s' % (response, response.text)
    if check:
      raise InternalServerError(err_msg)
    return False, err_msg
