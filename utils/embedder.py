from typing import Optional, Union

import nextcord

import config

DEFAULT_COLOR = nextcord.Colour.blurple()
MAX_EMBED_DESCRIPTION_LENGTH = 4096
MAX_EMBED_FIELD_TITLE_LENGTH = 256
MAX_EMBED_FIELD_FOOTER_LENGTH = 2048



def __trim(text: str, limit: int) -> str:
    """limit text to a certain number of characters"""
    return text[: limit - 3].strip() + "..." if len(text) > limit else text


def embed_success(
    title: str,
    description: Optional[str] = None,
    footer: Optional[str] = None,
    url: Union[str, None] = None,
    image: Optional[str] = None,
    thumbnail: Optional[str] = None,
) -> nextcord.Embed:
    """Embed a success message and an optional description, footer, and url"""
    return build_embed(title, description, footer, url, nextcord.Colour.green(), image, thumbnail)


def embed_warning(
    title: str,
    description: Optional[str] = None,
    footer: Optional[str] = None,
    url: Union[str, None] = None,
    image: Optional[str] = None,
    thumbnail: Optional[str] = None,
) -> nextcord.Embed:
    """Embed a warning message and an optional description, footer, and url"""
    return build_embed(title, description, footer, url, nextcord.Colour.gold(), image, thumbnail)


def embed_error(
    title: str,
    description: Optional[str] = None,
    footer: Optional[str] = None,
    url: Union[str, None] = None,
    image: Optional[str] = None,
    thumbnail: Optional[str] = None,
) -> nextcord.Embed:
    """Embed an error message and an optional description, footer, and url"""
    return build_embed(title, description, footer, url, nextcord.Colour.red(), image, thumbnail)


def build_embed(
    title: str,
    description: Optional[str] = None,
    footer: Optional[str] = None,
    url: Union[str, None] = None,
    colour: nextcord.Colour = DEFAULT_COLOR,
    image: Optional[str] = None,
    thumbnail: Optional[str] = None,
) -> nextcord.Embed:
    """Embed a message and an optional description, footer, and url"""
    # create the embed
    embed = nextcord.Embed(
        title=__trim(title, MAX_EMBED_FIELD_TITLE_LENGTH), url=url, colour=colour
    )
    if description:
        embed.description = __trim(description, MAX_EMBED_DESCRIPTION_LENGTH)
    if footer:
        embed.set_footer(text=__trim(footer, MAX_EMBED_FIELD_FOOTER_LENGTH))
    if image:
        embed.set_image(url=image)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    return embed


def promotion_embed() -> nextcord.Embed:
    """Referral offer shown to customers who ask for free commends.

    The original hardcoded a personal Trading 212 referral link and an offer
    that expired in July 2023. Everything now comes from config so the repo
    does not ship someone else's referral code; leave PROMO_INVITE_URL empty
    to disable the offer.
    """
    embed = nextcord.Embed(
        title=config.PROMO_TITLE,
        description=(
            f"{config.PROMO_DESCRIPTION}\n\n"
            f"[Click here to join {config.PROMO_PARTNER}]({config.PROMO_INVITE_URL})"
        ),
        color=config.PROMO_COLOR,
    )
    embed.add_field(
        name="Requirements:",
        value=(
            "> You need to have a valid **ID** and be more than **18** years old.\n"
            f"> Apply the promo code (`{config.PROMO_CODE}`) or use the invite link.\n"
            f"> Contact <@{config.OWNER_ID}> to redeem your commends."
        ),
        inline=False,
    )
    embed.add_field(
        name="Need more help?", value=f"Contact <@{config.OWNER_ID}>", inline=False
    )
    if config.PROMO_THUMBNAIL_URL:
        embed.set_thumbnail(url=config.PROMO_THUMBNAIL_URL)
    if config.PROMO_IMAGE_URL:
        embed.set_image(url=config.PROMO_IMAGE_URL)
    embed.set_footer(text=f"Promocode: {config.PROMO_CODE}")
    return embed



