import os
import base64
import json
from PIL import Image
from json.decoder import JSONDecodeError
from random import choice
from AnieXEricaMusic.helper.handler import register
from asyncio import sleep
from telethon.errors import MessageDeleteForbiddenError, MessageNotModifiedError
from telethon.tl.custom import Message
from telethon.tl.types import MessageService
from telethon.tl import types
from telethon.utils import get_display_name, get_peer_id
try:
    from aiohttp import ContentTypeError
except ImportError:
    ContentTypeError = None

try:
    from PIL import Image
except ImportError:
    Image = None

# Example color palette for backgrounds
all_col = ["#FFFFFF", "#FF5733", "#33FF57", "#3357FF"]

class Quotly:
    _API = "https://bot.lyo.su/quote/generate"
    _entities = {
        types.MessageEntityPhone: "phone_number",
        types.MessageEntityMention: "mention",
        types.MessageEntityBold: "bold",
        types.MessageEntityCashtag: "cashtag",
        types.MessageEntityStrike: "strikethrough",
        types.MessageEntityHashtag: "hashtag",
        types.MessageEntityEmail: "email",
        types.MessageEntityMentionName: "text_mention",
        types.MessageEntityUnderline: "underline",
        types.MessageEntityUrl: "url",
        types.MessageEntityTextUrl: "text_link",
        types.MessageEntityBotCommand: "bot_command",
        types.MessageEntityCode: "code",
        types.MessageEntityPre: "pre",
    }

    async def _format_quote(self, event, reply=None, sender=None, type_="private"):
        async def telegraph(file_):
            file = file_ + ".png"
            Image.open(file_).save(file, "PNG")
            files = {"file": open(file, "rb").read()}
            uri = (
                "https://telegra.ph"
                + (
                    await async_searcher(
                        "https://telegra.ph/upload", post=True, data=files, re_json=True
                    )
                )[0]["src"]
            )
            os.remove(file)
            os.remove(file_)
            return uri

        if reply:
            reply = {
                "name": get_display_name(reply.sender) or "Deleted Account",
                "text": reply.raw_text,
                "chatId": reply.chat_id,
            }
        else:
            reply = {}
        is_fwd = event.fwd_from
        name = None
        last_name = None
        if sender:
            id_ = get_peer_id(sender)
            name = get_display_name(sender)
        elif not is_fwd:
            id_ = event.sender_id
            sender = await event.get_sender()
            name = get_display_name(sender)
        else:
            id_, sender = None, None
            name = is_fwd.from_name
            if is_fwd.from_id:
                id_ = get_peer_id(is_fwd.from_id)
                try:
                    sender = await event.client.get_entity(id_)
                    name = get_display_name(sender)
                except ValueError:
                    pass
        if sender and hasattr(sender, "last_name"):
            last_name = sender.last_name
        entities = []
        if event.entities:
            for entity in event.entities:
                if type(entity) in self._entities:
                    enti_ = entity.to_dict()
                    del enti_["_"]
                    enti_["type"] = self._entities[type(entity)]
                    entities.append(enti_)
        message = {
            "entities": entities,
            "chatId": id_,
            "avatar": True,
            "from": {
                "id": id_,
                "first_name": (name or (sender.first_name if sender else None))
                or "Deleted Account",
                "last_name": last_name,
                "username": sender.username if sender else None,
                "language_code": "en",
                "title": name,
                "name": name or "Unknown",
                "type": type_,
            },
            "text": event.raw_text,
            "replyMessage": reply,
        }
        if event.document and event.document.thumbs:
            file_ = await event.download_media(thumb=-1)
            uri = await telegraph(file_)
            message["media"] = {"url": uri}

        return message

    async def create_quotly(
        self,
        event,
        url="https://qoute-api-akashpattnaik.koyeb.app/generate",
        reply={},
        bg=None,
        sender=None,
        OQAPI=True,
        file_name="quote.webp",
    ):
        """Create quotely's quote."""
        if not isinstance(event, list):
            event = [event]
        if OQAPI:
            url = Quotly._API
        if not bg:
            bg = "#1b1429"
        content = {
            "type": "quote",
            "format": "webp",
            "backgroundColor": bg,
            "width": 512,
            "height": 768,
            "scale": 2,
            "messages": [
                await self._format_quote(message, reply=reply, sender=sender)
                for message in event
            ],
        }
        try:
            request = await async_searcher(url, post=True, json=content, re_json=True)
        except ContentTypeError as er:
            if url != self._API:
                return await self.create_quotly(
                    self._API, post=True, json=content, re_json=True
                )
            raise er
        if request.get("ok"):
            with open(file_name, "wb") as file:
                image = base64.decodebytes(request["result"]["image"].encode("utf-8"))
                file.write(image)
            return file_name
        raise Exception(str(request))

quotly = Quotly()

async def async_searcher(
    url: str,
    post: bool = None,
    headers: dict = None,
    params: dict = None,
    json: dict = None,
    data: dict = None,
    ssl=None,
    re_json: bool = False,
    re_content: bool = False,
    real: bool = False,
    *args,
    **kwargs,
):
    try:
        import aiohttp
    except ImportError as e:
        print(e)
        
    async with aiohttp.ClientSession(headers=headers) as client:
        if post:
            data = await client.post(
                url, json=json, data=data, ssl=ssl, *args, **kwargs
            )
        else:
            data = await client.get(url, params=params, ssl=ssl, *args, **kwargs)
        if re_json:
            return await data.json()
        if re_content:
            return await data.read()
        if real:
            return data
        return await data.text()

def json_parser(data, indent=None, ascii=False):
    parsed = {}
    try:
        if isinstance(data, str):
            parsed = json.loads(str(data))
            if indent:
                parsed = json.dumps(
                    json.loads(str(data)), indent=indent, ensure_ascii=ascii
                )
        elif isinstance(data, dict):
            parsed = data
            if indent:
                parsed = json.dumps(data, indent=indent, ensure_ascii=ascii)
    except JSONDecodeError:
        parsed = eval(data)
    return parsed


def check_filename(filroid):
    if os.path.exists(filroid):
        no = 1
        while True:
            ult = "{0}_{2}{1}".format(*os.path.splitext(filroid) + (no,))
            if os.path.exists(ult):
                no += 1
            else:
                return ult
    return filroid

#edit or reply
async def eor(event, text=None, **args):
    time = args.get("time", None)
    edit_time = args.get("edit_time", None)
    if "edit_time" in args:
        del args["edit_time"]
    if "time" in args:
        del args["time"]
    if "link_preview" not in args:
        args["link_preview"] = False
    args["reply_to"] = event.reply_to_msg_id or event
    if event.out and not isinstance(event, MessageService):
        if edit_time:
            await sleep(edit_time)
        if "file" in args and args["file"] and not event.media:
            await event.delete()
            try:
                ok = await event.client.send_message(event.chat_id, text, **args)
            except MessageNotModifiedError:
                pass
        else:
            try:
                try:
                    del args["reply_to"]
                except KeyError:
                    pass
                ok = await event.edit(text, **args)
            except MessageNotModifiedError:
                pass
    else:
        ok = await event.client.send_message(event.chat_id, text, **args)

    if time:
        await sleep(time)
        return await ok.delete()
    return ok


async def eod(event, text=None, **kwargs):
    kwargs["time"] = kwargs.get("time", 8)
    return await eor(event, text, **kwargs)


async def _try_delete(event):
    try:
        return await event.delete()
    except (MessageDeleteForbiddenError):
        pass
    except BaseException as er:
        print(er)


setattr(Message, "eor", eor)
setattr(Message, "try_delete", _try_delete)

@register(pattern="^/q(?: |$)(.*)")
async def quott_(event):
    match = event.pattern_match.group(1).strip()
    if not event.is_reply:
        return await event.eor("𝖯𝗅𝖾𝖺𝗌𝖾 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗆𝖾𝗌𝗌𝖺𝗀𝖾")
    msg = await event.reply("𝖢𝗋𝖾𝖺𝗍𝗂𝗇𝗀 𝗊𝗎𝗈𝗍𝖾 𝗉𝗅𝖾𝖺𝗌𝖾 𝗐𝖺𝗂𝗍....")
    reply = await event.get_reply_message()
    replied_to, reply_ = None, None
    if match:
        spli_ = match.split(maxsplit=1)
        if (spli_[0] in ["r", "reply"]) or (
            spli_[0].isdigit() and int(spli_[0]) in range(1, 21)
        ):
            if spli_[0].isdigit():
                if not event.client._bot:
                    reply_ = await event.client.get_messages(
                        event.chat_id,
                        min_id=event.reply_to_msg_id - 1,
                        reverse=True,
                        limit=int(spli_[0]),
                    )
                else:
                    id_ = reply.id
                    reply_ = []
                    for msg_ in range(id_, id_ + int(spli_[0])):
                        msh = await event.client.get_messages(event.chat_id, ids=msg_)
                        if msh:
                            reply_.append(msh)
            else:
                replied_to = await reply.get_reply_message()
            try:
                match = spli_[1]
            except IndexError:
                match = None
    user = None
    if not reply_:
        reply_ = reply
    if match:
        match = match.split(maxsplit=1)
    if match:
        if match[0].startswith("@") or match[0].isdigit():
            try:
                match_ = await event.client.parse_id(match[0])
                user = await event.client.get_entity(match_)
            except ValueError:
                pass
            match = match[1] if len(match) == 2 else None
        else:
            match = match[0]
    if match == "random":
        match = choice(all_col)
    try:
        file = await quotly.create_quotly(
            reply_, bg=match, reply=replied_to, sender=user
        )
    except Exception as er:
        return await msg.edit(str(er))
    message = await reply.reply("", file=file)
    os.remove(file)
    await msg.delete()
    return message

__module__ = "𝖰𝗎𝗈𝗍𝗅𝗒"


__help__ = """**𝖢𝗋𝖾𝖺𝗍𝖾 𝖻𝖾𝖺𝗎𝗍𝗂𝖿𝗎𝗅 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 𝗊𝗎𝗈𝗍𝖾𝗌:**

   ✧ `/𝗊` **:** 𝖱𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 𝗐𝗂𝗍𝗁 𝗍𝗁𝗂𝗌 𝖼𝗈𝗆𝗆𝖺𝗇𝖽 𝗍𝗈 𝗀𝖾𝗇𝖾𝗋𝖺𝗍𝖾 𝖺 𝗊𝗎𝗈𝗍𝖾.
   ✧ `/𝗊 <𝖻𝖺𝖼𝗄𝗀𝗋𝗈𝗎𝗇𝖽 𝖼𝗈𝗅𝗈𝗋>` **:** 𝖢𝗎𝗌𝗍𝗈𝗆𝗂𝗓𝖾 𝗍𝗁𝖾 𝗊𝗎𝗈𝗍𝖾'𝗌 𝖻𝖺𝖼𝗄𝗀𝗋𝗈𝗎𝗇𝖽 𝖼𝗈𝗅𝗈𝗋 𝗎𝗌𝗂𝗇𝗀 𝖺 𝗁𝖾𝗑 𝖼𝗈𝖽𝖾 𝗈𝗋 𝖺 𝖼𝗈𝗅𝗈𝗋 𝗇𝖺𝗆𝖾 (𝖾.𝗀., `/𝗊 #𝖥𝖥𝟧𝟩𝟥𝟥`).
   ✧ `/𝗊 𝗋𝖺𝗇𝖽𝗈𝗆` **:** 𝖦𝖾𝗇𝖾𝗋𝖺𝗍𝖾 𝖺 𝗊𝗎𝗈𝗍𝖾 𝗐𝗂𝗍𝗁 𝖺 𝗋𝖺𝗇𝖽𝗈𝗆 𝖻𝖺𝖼𝗄𝗀𝗋𝗈𝗎𝗇𝖽 𝖼𝗈𝗅𝗈𝗋.
   ✧ `/𝗊 <𝗇𝗎𝗆𝖻𝖾𝗋>` **:** 𝖦𝖾𝗇𝖾𝗋𝖺𝗍𝖾 𝖺 𝗊𝗎𝗈𝗍𝖾 𝗂𝗇𝖼𝗅𝗎𝖽𝗂𝗇𝗀 𝗍𝗁𝖾 𝗌𝗉𝖾𝖼𝗂𝖿𝗂𝖾𝖽 𝗇𝗎𝗆𝖻𝖾𝗋 𝗈𝖿 𝗉𝗋𝖾𝗏𝗂𝗈𝗎𝗌 𝗆𝖾𝗌𝗌𝖺𝗀𝖾𝗌 (𝖾.𝗀., `/𝗊 𝟧` 𝗍𝗈 𝗂𝗇𝖼𝗅𝗎𝖽𝖾 𝟧 𝗆𝖾𝗌𝗌𝖺𝗀𝖾𝗌).
   ✧ `/𝗊 𝗋` **:** 𝖦𝖾𝗇𝖾𝗋𝖺𝗍𝖾 𝖺 𝗊𝗎𝗈𝗍𝖾 𝗍𝗁𝖺𝗍 𝗂𝗇𝖼𝗅𝗎𝖽𝖾𝗌 𝗍𝗁𝖾 𝗋𝖾𝗉𝗅𝗂𝖾𝖽-𝗍𝗈 𝗆𝖾𝗌𝗌𝖺𝗀𝖾.
 
**𝖤𝗑𝖺𝗆𝗉𝗅𝖾𝗌:**
   ✧ `/𝗊` **:** 𝖢𝗋𝖾𝖺𝗍𝖾 𝖺 𝗊𝗎𝗈𝗍𝖾 𝖿𝗋𝗈𝗆 𝗍𝗁𝖾 𝗋𝖾𝗉𝗅𝗂𝖾𝖽 𝗆𝖾𝗌𝗌𝖺𝗀𝖾.
   ✧ `/𝗊 #𝟣𝖻𝟣𝟦𝟤𝟫` **:** 𝖢𝗋𝖾𝖺𝗍𝖾 𝖺 𝗊𝗎𝗈𝗍𝖾 𝗐𝗂𝗍𝗁 𝖺 𝖽𝖺𝗋𝗄 𝗉𝗎𝗋𝗉𝗅𝖾 𝖻𝖺𝖼𝗄𝗀𝗋𝗈𝗎𝗇𝖽.
   ✧ `/𝗊 𝗋𝖺𝗇𝖽𝗈𝗆` **:** 𝖢𝗋𝖾𝖺𝗍𝖾 𝖺 𝗊𝗎𝗈𝗍𝖾 𝗐𝗂𝗍𝗁 𝖺 𝗋𝖺𝗇𝖽𝗈𝗆𝗅𝗒 𝗌𝖾𝗅𝖾𝖼𝗍𝖾𝖽 𝖻𝖺𝖼𝗄𝗀𝗋𝗈𝗎𝗇𝖽 𝖼𝗈𝗅𝗈𝗋.
   ✧ `/𝗊 𝟥` **:** 𝖢𝗋𝖾𝖺𝗍𝖾 𝖺 𝗊𝗎𝗈𝗍𝖾 𝖿𝗋𝗈𝗆 𝗍𝗁𝖾 𝗋𝖾𝗉𝗅𝗂𝖾𝖽 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 𝖺𝗇𝖽 𝗍𝗁𝖾 𝗍𝗐𝗈 𝗉𝗋𝖾𝖼𝖾𝖽𝗂𝗇𝗀 𝗆𝖾𝗌𝗌𝖺𝗀𝖾𝗌.
   ✧ `/𝗊 𝗋𝖾𝗉𝗅𝗒` **:** 𝖨𝗇𝖼𝗅𝗎𝖽𝖾 𝗍𝗁𝖾 𝗋𝖾𝗉𝗅𝗂𝖾𝖽-𝗍𝗈 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 𝗂𝗇 𝗍𝗁𝖾 𝗊𝗎𝗈𝗍𝖾.
 
"""