import json
import typing as t

import pandas as pd

from rigging.chat import Chat
from rigging.message import Message


def chats_to_df(chats: list[Chat]) -> pd.DataFrame:
    """
    Convert a list of Chat objects into a pandas DataFrame.

    Note:
        The messages will be flatted and can be joined by the
        chat_id column.

    Args:
        chats: A list of Chat objects.

    Returns:
        A pandas DataFrame containing the chat data.

    """
    data: list[dict[t.Any, t.Any]] = []
    for chat in chats:
        generator_id = chat.generator_id
        metadata = json.dumps(chat.metadata)
        generated = False
        for messages in [chat.messages, chat.generated]:
            for message in messages:
                message_dict = message.model_dump()
                message_dict["message_id"] = message_dict.pop("uuid")
                data.append(
                    {
                        "chat_id": chat.uuid,
                        "chat_metadata": metadata,
                        "chat_generator_id": generator_id,
                        "chat_timestamp": chat.timestamp,
                        "generated": generated,
                        **message_dict,
                    }
                )
            generated = True

    df = pd.DataFrame(data).astype(
        {
            "chat_id": "string",
            "chat_metadata": "string",
            "chat_generator_id": "string",
            "chat_timestamp": "datetime64[ms]",
            "generated": "bool",
            "message_id": "string",
            "role": "category",
            "content": "string",
            "parts": "string",
        }
    )

    # TODO: Come back to indexing

    return df


def df_to_chats(df: pd.DataFrame) -> list[Chat]:
    """
    Convert a pandas DataFrame into a list of Chat objects.

    Note:
        The DataFrame should have the same structure as the one
        generated by the `chats_to_df` function.

    Args:
        df: A pandas DataFrame containing the chat data.

    Returns:
        A list of Chat objects.

    """
    chats = []
    for chat_id, chat_group in df.groupby("chat_id"):
        chat_data = chat_group.iloc[0]
        messages = []
        generated = []

        for _, message_data in chat_group.iterrows():
            message = Message(
                role=message_data["role"],
                content=message_data["content"],
                parts=json.loads(message_data["parts"]),
                **{"uuid": message_data["message_id"]},
            )
            if message_data["generated"]:
                generated.append(message)
            else:
                messages.append(message)

        chat = Chat(
            uuid=chat_id,
            timestamp=chat_data["chat_timestamp"],
            messages=messages,
            generated=generated,
            metadata=json.loads(chat_data["chat_metadata"]),
            **{"generator_id": chat_data["chat_generator_id"]},
        )
        chats.append(chat)

    return chats
