"""X (Twitter) API v2 publisher using OAuth 1.0a User Context and thread support."""

import logging
from typing import Optional
import tweepy

from src.core.config import Settings
from src.core.models import CTIAnalysisResult
from src.publishers.base import BasePublisher

logger = logging.getLogger("nullday.publishers.x_twitter")


class XPublisher(BasePublisher):
    """Publishes high-impact urgent CTI alerts and thread replies to X/Twitter."""

    def __init__(
        self,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
    ):
        self.consumer_key = consumer_key or Settings.X_CONSUMER_KEY
        self.consumer_secret = consumer_secret or Settings.X_CONSUMER_SECRET
        self.access_token = access_token or Settings.X_ACCESS_TOKEN
        self.access_token_secret = access_token_secret or Settings.X_ACCESS_TOKEN_SECRET

        self._client: Optional[tweepy.Client] = None
        if self._has_credentials():
            try:
                self._client = tweepy.Client(
                    consumer_key=self.consumer_key,
                    consumer_secret=self.consumer_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret,
                )
            except Exception as e:
                logger.error(f"Failed to initialize Tweepy client: {e}")

    def _has_credentials(self) -> bool:
        return bool(
            self.consumer_key
            and self.consumer_secret
            and self.access_token
            and self.access_token_secret
        )

    def publish(self, data: CTIAnalysisResult, dry_run: bool = False) -> bool:
        """Publish alert tweet and optional thread reply to X/Twitter."""
        payload = data.x_payload
        tweet_text = payload.tweet_text.strip()
        thread_reply = payload.thread_reply.strip() if payload.thread_reply else None

        if dry_run or not self._client:
            print("\n" + "=" * 70)
            print("[DRY-RUN] X / TWITTER ALERT PREVIEW")
            print("=" * 70)
            print(f"Root Tweet ({len(tweet_text)} / 280 chars):")
            print(f">>> {tweet_text}")
            if thread_reply:
                print(f"\nThread Reply ({len(thread_reply)} / 280 chars):")
                print(f">>> {thread_reply}")
            print("=" * 70 + "\n")
            return True

        logger.info("Publishing alert tweet to X/Twitter API v2...")
        try:
            # 1. Post root alert tweet
            response = self._client.create_tweet(text=tweet_text)
            root_id = response.data["id"]
            logger.info(f"Root tweet published successfully (Tweet ID: {root_id}).")

            # 2. Post thread reply if configured
            if thread_reply:
                logger.info(f"Posting thread follow-up to Tweet ID {root_id}...")
                reply_resp = self._client.create_tweet(
                    text=thread_reply,
                    in_reply_to_tweet_id=root_id,
                )
                logger.info(f"Thread reply published (Tweet ID: {reply_resp.data['id']}).")

            return True

        except Exception as e:
            logger.error(f"Failed to publish tweet via X API v2: {e}", exc_info=True)
            return False
