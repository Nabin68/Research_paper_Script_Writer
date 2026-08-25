"""Every Instagram-specific address in one file: endpoints, JSON field paths, DOM selectors.

The brief says a UI change should mean editing one file. That is the goal here,
but it is worth being precise about what "selector" means for this scraper,
because the answer shapes the whole design.

Instagram renders almost nothing useful into the DOM. Like counts on a reel,
play counts, the exact publish timestamp, tagged users, the direct video URL —
none of it is reliably present as text you can read off the page, and what is
present is wrapped in class names that are regenerated on every deploy
(`x1i10hfl`, `_aacl`). Scraping that is a treadmill.

What Instagram's own web app does instead is call its internal JSON API and
render from the response. This package does the same thing: it holds a real
logged-in session, calls those same endpoints, and parses the JSON. So the
things that break when Instagram changes are, in order of likelihood:

  1. `Paths`     — where a field sits inside the JSON. Changes occasionally.
  2. `Endpoints` — the URLs themselves. Changes rarely.
  3. `Dom`       — only used by the login detector and the last-resort fallback.

All three live below. Nothing addressed to Instagram is written anywhere else.
"""

from __future__ import annotations

from typing import Final

BASE_URL: Final = "https://www.instagram.com"


class Endpoints:
    """Instagram URLs. `{}` placeholders are filled with `.format(...)`."""

    HOME: Final = BASE_URL + "/"
    LOGIN: Final = BASE_URL + "/accounts/login/"
    PROFILE: Final = BASE_URL + "/{username}/"
    POST: Final = BASE_URL + "/p/{shortcode}/"
    REEL: Final = BASE_URL + "/reel/{shortcode}/"

    # Profile header + first page of the timeline, in one call. This is the same
    # request the web app fires when you open a profile.
    WEB_PROFILE_INFO: Final = BASE_URL + "/api/v1/users/web_profile_info/?username={username}"

    # Paged timeline. Preferred over paginating web_profile_info's GraphQL edges,
    # which needs a `query_hash` that Instagram rotates; this one is addressed by
    # user id and has been stable for years. `max_id` is the pagination cursor.
    USER_FEED: Final = BASE_URL + "/api/v1/feed/user/{user_id}/?count={count}"
    USER_FEED_PAGED: Final = USER_FEED + "&max_id={max_id}"

    # Single post by media id. The media id is computed from the shortcode
    # locally (see utils.shortcode_to_media_id), so this needs no lookup call and
    # no rotating query hash — the most stable path to one post's full metadata.
    MEDIA_INFO: Final = BASE_URL + "/api/v1/media/{media_id}/info/"

    # Cheap "am I still logged in?" probe: 200 with a JSON body when the session
    # is live, 401/redirect when it is not.
    CURRENT_USER: Final = BASE_URL + "/api/v1/accounts/current_user/"


class Headers:
    """Headers Instagram's internal API requires. Missing `x-ig-app-id` means 401."""

    API: Final = {
        "x-ig-app-id": "{app_id}",
        "x-requested-with": "XMLHttpRequest",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
    }


class Paths:
    """Where each field lives inside Instagram's JSON.

    Dotted paths, read by `utils.dig`. A `[0]` segment indexes a list. When
    several paths are listed for one field they are tried in order — Instagram
    serves different shapes to different sessions and has renamed several of
    these in place (`edge_liked_by` -> `edge_media_preview_like`), so a list of
    candidates is what keeps one rename from emptying a column.
    """

    # -- envelopes ---------------------------------------------------------- #
    PROFILE_ROOT: Final = ("data.user",)
    FEED_ITEMS: Final = ("items",)
    FEED_NEXT_CURSOR: Final = ("next_max_id",)
    FEED_MORE_AVAILABLE: Final = ("more_available",)
    MEDIA_ITEM: Final = ("items[0]",)
    TIMELINE_EDGES: Final = ("edge_owner_to_timeline_media.edges",)

    # Post JSON captured off a page navigation, when the API paths are refused.
    PAGE_MEDIA: Final = (
        "data.xdt_shortcode_media",
        "data.shortcode_media",
        "graphql.shortcode_media",
        "items[0]",
    )

    # -- profile ------------------------------------------------------------ #
    USER_ID: Final = ("id", "pk", "pk_id")
    USERNAME: Final = ("username",)
    FULL_NAME: Final = ("full_name",)
    BIOGRAPHY: Final = ("biography",)
    FOLLOWERS: Final = ("edge_followed_by.count", "follower_count")
    FOLLOWING: Final = ("edge_follow.count", "following_count")
    POST_COUNT: Final = ("edge_owner_to_timeline_media.count", "media_count")
    PROFILE_PIC: Final = ("profile_pic_url_hd", "profile_pic_url")
    IS_VERIFIED: Final = ("is_verified",)
    IS_PRIVATE: Final = ("is_private",)
    IS_BUSINESS: Final = ("is_business_account",)
    CATEGORY: Final = ("category_name", "category")
    EXTERNAL_URL: Final = ("external_url",)
    BIO_LINKS: Final = ("bio_links",)
    FOLLOWED_BY_VIEWER: Final = ("followed_by_viewer", "friendship_status.following")

    # -- post: private-API shape (items[] from feed/user and media/info) ----- #
    API_ID: Final = ("pk", "id")
    API_SHORTCODE: Final = ("code",)
    API_CAPTION: Final = ("caption.text",)
    API_TAKEN_AT: Final = ("taken_at",)
    API_LIKES: Final = ("like_count",)
    API_COMMENTS: Final = ("comment_count",)
    API_VIEWS: Final = ("play_count", "ig_play_count", "view_count")
    API_MEDIA_TYPE: Final = ("media_type",)
    API_PRODUCT_TYPE: Final = ("product_type",)
    API_OWNER: Final = ("user.username", "owner.username")
    API_THUMBNAIL: Final = ("image_versions2.candidates[0].url",)
    API_VIDEO: Final = ("video_versions[0].url",)
    API_CAROUSEL: Final = ("carousel_media",)
    API_LOCATION: Final = ("location.name",)
    API_TAGGED: Final = ("usertags.in",)
    API_TAGGED_USER: Final = ("user.username",)

    # -- post: GraphQL shape (timeline edges, page captures) ----------------- #
    GQL_ID: Final = ("id",)
    GQL_SHORTCODE: Final = ("shortcode",)
    GQL_CAPTION: Final = ("edge_media_to_caption.edges[0].node.text",)
    GQL_TAKEN_AT: Final = ("taken_at_timestamp",)
    GQL_LIKES: Final = ("edge_media_preview_like.count", "edge_liked_by.count")
    GQL_COMMENTS: Final = ("edge_media_to_comment.count", "edge_media_preview_comment.count")
    GQL_VIEWS: Final = ("video_play_count", "video_view_count")
    GQL_TYPENAME: Final = ("__typename",)
    GQL_IS_VIDEO: Final = ("is_video",)
    GQL_OWNER: Final = ("owner.username",)
    GQL_THUMBNAIL: Final = ("display_url", "thumbnail_src")
    GQL_VIDEO: Final = ("video_url",)
    GQL_CAROUSEL: Final = ("edge_sidecar_to_children.edges",)
    GQL_LOCATION: Final = ("location.name",)
    GQL_TAGGED: Final = ("edge_media_to_tagged_user.edges",)
    GQL_TAGGED_USER: Final = ("node.user.username",)


class MediaTypeCodes:
    """Instagram's numeric `media_type`, and the `product_type` that marks a reel."""

    IMAGE: Final = 1
    VIDEO: Final = 2
    CAROUSEL: Final = 8
    REEL_PRODUCT_TYPES: Final = frozenset({"clips", "igtv"})
    GQL_IMAGE: Final = "GraphImage"
    GQL_VIDEO: Final = "GraphVideo"
    GQL_CAROUSEL: Final = "GraphSidecar"


class Dom:
    """CSS selectors. Used only for login detection and the last-resort fallback.

    Deliberately anchored to structural attributes (`role`, `href`, `name`,
    `aria-label`) rather than to Instagram's generated class names, which change
    on every deploy and are worthless as selectors.
    """

    # -- login flow --------------------------------------------------------- #
    LOGIN_USERNAME_INPUT: Final = "input[name='username']"
    LOGIN_PASSWORD_INPUT: Final = "input[name='password']"
    LOGIN_SUBMIT: Final = "button[type='submit']"
    LOGIN_ERROR: Final = "#slfErrorAlert, [role='alert']"

    # Present only when logged in — the nav bar's profile/home affordances.
    LOGGED_IN_MARKERS: Final = (
        "svg[aria-label='Home']",
        "a[href='/explore/']",
        "[aria-label='Profile']",
        "nav a[href*='/direct/']",
    )
    # Present only when logged out.
    LOGGED_OUT_MARKERS: Final = (
        "input[name='username']",
        "a[href*='/accounts/login/']",
    )
    # Checkpoint / 2FA / "suspicious login attempt" interstitials.
    CHALLENGE_MARKERS: Final = (
        "input[name='verificationCode']",
        "input[name='security_code']",
        "form[action*='challenge']",
        "[data-testid='2fa-input']",
    )
    # Cookie banner and "Save your login info?" dialog, both of which sit on top
    # of the page after login and block the logged-in markers from being visible.
    DISMISS_BUTTONS: Final = (
        "button:has-text('Allow all cookies')",
        "button:has-text('Accept all')",
        "button:has-text('Not now')",
        "button:has-text('Not Now')",
    )

    # -- profile fallback --------------------------------------------------- #
    PROFILE_HEADER: Final = "header section"
    PROFILE_NOT_FOUND: Final = "text=Sorry, this page isn't available."
    PROFILE_PRIVATE: Final = "text=This account is private"
    PROFILE_STAT_ITEMS: Final = "header section ul li"
    PROFILE_BIO: Final = "header section h1 + div, header section > div > span"
    PROFILE_IMAGE: Final = "header img"
    PROFILE_VERIFIED: Final = "svg[aria-label='Verified']"

    # -- post fallback ------------------------------------------------------ #
    POST_ARTICLE: Final = "article"
    POST_CAPTION: Final = "article h1, article ul li h1"
    POST_TIME: Final = "article time[datetime]"
    POST_LIKES: Final = "article section span a[href$='/liked_by/'] span, article section span"
    POST_VIDEO: Final = "article video"
    POST_IMAGE: Final = "article img[srcset]"
    POST_UNAVAILABLE: Final = "text=Sorry, this page isn't available."

    # -- rate limiting ------------------------------------------------------ #
    RATE_LIMIT_MARKERS: Final = (
        "text=Please wait a few minutes before you try again",
        "text=Try Again Later",
    )


# Response bodies that mean "rate limited" even when the status code is 200.
RATE_LIMIT_BODY_MARKERS: Final = (
    "please wait a few minutes",
    "try again later",
    "rate limited",
)
