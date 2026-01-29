"""Configuration management for SMZDM Bot.

Configuration is loaded from environment variables using Pydantic Settings.

Environment Variables:
    SMZDM_COOKIE: Cookie string (single user mode)
    SMZDM_SK: Optional security key
    SMZDM_USERS: JSON array for multi-user mode
        Example: '[{"cookie": "...", "sk": "..."}, {"cookie": "..."}]'

    Notification:
    SMZDM_PUSH_PLUS_TOKEN: PushPlus token
    SMZDM_SC_KEY: ServerChan key
    SMZDM_WECOM_WEBHOOK: WeCom bot webhook URL
    SMZDM_TG_BOT_TOKEN: Telegram bot token
    SMZDM_TG_USER_ID: Telegram user/chat ID
    SMZDM_TG_API_BASE: Custom Telegram API base URL

    Scheduler:
    SMZDM_SCH_HOUR: Hour to run (0-23)
    SMZDM_SCH_MINUTE: Minute to run (0-59)
    SMZDM_TIMEZONE: Timezone (default: Asia/Shanghai)
"""

import json
from pathlib import Path

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from smzdm_bot.exceptions import ConfigurationError


def _find_dotenv() -> Path | None:
    """Find .env file by searching up from cwd or using package location."""
    # Try current directory first
    cwd = Path.cwd()
    if (cwd / ".env").exists():
        return cwd / ".env"

    # Try package directory (for installed package)
    pkg_dir = Path(__file__).parent.parent.parent.parent  # src/smzdm_bot/config -> root
    if (pkg_dir / ".env").exists():
        return pkg_dir / ".env"

    return None


class UserConfig(BaseModel):
    """Configuration for a single user account.

    Attributes:
        cookie: SMZDM cookie string.
        sk: Optional security key from app.
        name: Optional user identifier for logging.
    """

    cookie: str
    sk: str = ""
    name: str = ""

    @field_validator("cookie")
    @classmethod
    def validate_cookie(cls, v: str) -> str:
        """Ensure cookie is not empty."""
        if not v or not v.strip():
            raise ValueError("Cookie cannot be empty")
        return v.strip()


class NotifyConfig(BaseModel):
    """Notification service configuration.

    All fields are optional. Leave empty to disable a provider.
    """

    push_plus_token: str = ""
    sc_key: str = ""
    wecom_webhook: str = ""
    tg_bot_token: str = ""
    tg_user_id: str = ""
    tg_api_base: str = ""

    @property
    def has_any_provider(self) -> bool:
        """Check if at least one notification provider is configured."""
        return any(
            [
                self.push_plus_token,
                self.sc_key,
                self.wecom_webhook,
                self.tg_bot_token and self.tg_user_id,
            ]
        )


class SchedulerConfig(BaseModel):
    """Scheduler configuration."""

    hour: int | None = None
    minute: int | None = None
    timezone: str = "Asia/Shanghai"


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Uses SMZDM_ prefix for all environment variables.

    Example:
        export SMZDM_COOKIE="your_cookie_here"
        export SMZDM_PUSH_PLUS_TOKEN="your_token"
    """

    # Single user mode
    cookie: str = ""
    sk: str = ""

    # Multi-user mode (JSON array)
    users: str = ""  # JSON string: '[{"cookie": "...", "sk": "..."}]'

    # Notification settings
    push_plus_token: str = ""
    sc_key: str = ""
    wecom_webhook: str = ""
    tg_bot_token: str = ""
    tg_user_id: str = ""
    tg_api_base: str = ""

    # Scheduler settings
    sch_hour: int | None = None
    sch_minute: int | None = None
    timezone: str = "Asia/Shanghai"

    # Debug mode
    debug: bool = False

    model_config = SettingsConfigDict(
        env_prefix="SMZDM_",
        env_file=_find_dotenv(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_users(self) -> list[UserConfig]:
        """Get list of user configurations.

        Supports multiple formats:
        1. SMZDM_USERS (JSON array): '[{"cookie": "...", "sk": "...", "name": "..."}]'
        2. SMZDM_USER1_COOKIE, SMZDM_USER2_COOKIE, ... (numbered format)
        3. SMZDM_COOKIE (single user fallback)

        Returns:
            List of UserConfig objects.

        Raises:
            ConfigurationError: If no users are configured.
        """
        users: list[UserConfig] = []

        # Method 1: Try JSON format (SMZDM_USERS)
        if self.users:
            try:
                users_data = json.loads(self.users)
                if isinstance(users_data, list):
                    for i, user_data in enumerate(users_data):
                        if isinstance(user_data, dict) and user_data.get("cookie"):
                            users.append(
                                UserConfig(
                                    cookie=user_data["cookie"],
                                    sk=user_data.get("sk", ""),
                                    name=user_data.get("name", f"User{i + 1}"),
                                )
                            )
            except json.JSONDecodeError as e:
                raise ConfigurationError(
                    f"Invalid SMZDM_USERS JSON format: {e}",
                    details={"users": self.users[:100]},
                ) from e

        # Method 2: Try numbered format (SMZDM_USER1_COOKIE, SMZDM_USER2_COOKIE, ...)
        # This requires accessing the raw environment variables
        if not users:
            import os
            user_num = 1
            while True:
                cookie_key = f"SMZDM_USER{user_num}_COOKIE"
                cookie = os.environ.get(cookie_key, "").strip()
                if not cookie:
                    break  # No more users

                sk_key = f"SMZDM_USER{user_num}_SK"
                name_key = f"SMZDM_USER{user_num}_NAME"
                sk = os.environ.get(sk_key, "").strip()
                name = os.environ.get(name_key, "").strip() or f"User{user_num}"

                users.append(
                    UserConfig(
                        cookie=cookie,
                        sk=sk,
                        name=name,
                    )
                )
                user_num += 1

        # Method 3: Fall back to single user mode (SMZDM_COOKIE)
        if not users and self.cookie:
            users.append(
                UserConfig(
                    cookie=self.cookie,
                    sk=self.sk,
                    name="default",
                )
            )

        if not users:
            raise ConfigurationError(
                "No users configured. Set SMZDM_COOKIE, SMZDM_USERS, or SMZDM_USER1_COOKIE environment variable.",
            )

        return users

    def get_notify_config(self) -> NotifyConfig:
        """Get notification configuration."""
        return NotifyConfig(
            push_plus_token=self.push_plus_token,
            sc_key=self.sc_key,
            wecom_webhook=self.wecom_webhook,
            tg_bot_token=self.tg_bot_token,
            tg_user_id=self.tg_user_id,
            tg_api_base=self.tg_api_base,
        )

    def get_scheduler_config(self) -> SchedulerConfig:
        """Get scheduler configuration."""
        return SchedulerConfig(
            hour=self.sch_hour,
            minute=self.sch_minute,
            timezone=self.timezone,
        )


# Global settings instance (lazy loaded)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance.

    Returns:
        Settings instance loaded from environment.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment.

    Useful for testing or when environment changes.

    Returns:
        Fresh Settings instance.
    """
    global _settings
    _settings = Settings()
    return _settings


__all__ = [
    "NotifyConfig",
    "SchedulerConfig",
    "Settings",
    "UserConfig",
    "get_settings",
    "reload_settings",
]
