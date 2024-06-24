from pywebio.input import input, input_group, actions, file_upload
from pywebio.output import put_markdown, output, put_scrollable, put_image, put_buttons, toast
from pywebio.session import run_async, run_js
import asyncio
import base64

online_users = set()
chat_msgs = []
max_message_count = 100


async def refresh_msg(nick, msg_box):
    global chat_msgs
    last_idx = len(chat_msgs)
    while True:
        await asyncio.sleep(1)

        for m in chat_msgs[last_idx:]:
            if m[0] == nick:
                msg_box.append(put_markdown(f"**{m[0]}:** {m[1]}"))
            else:
                if m[1].startswith("!["):
                    msg_box.append(put_markdown(f"**{m[0]}:** {m[1]}"))
                else:
                    msg_box.append(put_markdown(f"**{m[0]}:** {m[1]}"))

        if len(chat_msgs) > max_message_count:
            chat_msgs = chat_msgs[len(chat_msgs) // 2:]

        last_idx = len(chat_msgs)


async def main():
    global chat_msgs

    put_markdown("## 🗣 Добро пожаловать в онлайн чат!")

    msg_box = output()
    put_scrollable(msg_box, height=600, keep_bottom=True)

    nickname = await input("Войти в чат", required=True, placeholder="Ваше имя",
                           validate=lambda n: "Такой ник уже используется!" if n in online_users or n == '📢' else None)
    online_users.add(nickname)

    chat_msgs.append((nickname, f'присоединился к чату!'))
    msg_box.append(put_markdown(f'❗ **{nickname}** присоединился к чату'))

    refresh_task = run_async(refresh_msg(nickname, msg_box))

    while True:
        data = await input_group("💭 Новое сообщение", [
            input(placeholder="Текст сообщения ...", name="msg", autocomplete="off"),
            file_upload("Отправить картинку", name="image", max_size="5M", accept=".png,.jpg,.jpeg"),
            actions(name="cmd", buttons=["Отправить", {'label': "Выйти из чата", 'type': 'cancel'}])
        ], validate=lambda m: ('msg', "Введите текст сообщения!") if m["cmd"] == "Отправить" and not m['msg'] and not m['image'] else None)

        if data is None:
            break

        if 'image' in data and data['image']:
            try:
                image_filename = data['image'].get('filename')
                image_data = data['image'].get('content')
                chat_msgs.append((nickname, f"![{image_filename}](data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')})" ))
            except Exception as e:
                chat_msgs.append((nickname, f"*Ошибка при загрузке картинки: {e}*"))
        elif 'msg' in data and data['msg']:
            chat_msgs.append((nickname, data['msg']))

    refresh_task.close()

    online_users.remove(nickname)
    toast("Вы вышли из чата!")
    chat_msgs.append((f'❌', f'Пользователь {nickname} покинул чат!'))
    msg_box.append(put_markdown(f'❌ **{nickname}** покинул чат!'))

    put_buttons(['Перезайти'], onclick=lambda btn: run_js('window.location.reload()'))

if __name__ == "__main__":
    from pywebio import start_server
    start_server(main, debug=True, port=8080)
