from tortoise import Model, fields


class ThankModel(Model):
    id = fields.IntField(pk=True)
    guild = fields.ForeignKeyField(
        model_name="main.GuildModel",
        related_name="all_thanks",
        description="Guild in which the user was thanked",
    )
    thanker = fields.ForeignKeyField(
        model_name="main.UserModel",
        related_name="sent_thanks",
        description="The member who sent the thanks",
    )
    thanked = fields.ForeignKeyField(
        model_name="main.UserModel",
        related_name="thanks",
        description="The member who was thanked",
    )
    time = fields.DatetimeField(auto_now_add=True)
    description = fields.CharField(max_length=100)

    class Meta:
        table = "thanks"
        table_description = "Represents a 'thank' given from one user to another"


class GuildModel(Model):
    id = fields.BigIntField(pk=True, description="Discord ID of the guild")
    all_thanks: fields.ForeignKeyRelation[ThankModel]
    prefix = fields.CharField(max_length=10, description="Custom prefix of the guild")

    class Meta:
        table = "guilds"
        table_description = "Represents a discord guild's settings"


class UserModel(Model):
    id = fields.BigIntField(pk=True, description="Discord ID of the user")
    # External references
    github_oauth_token = fields.CharField(
        max_length=50, null=True, description="Github OAuth2 access token of the user"
    )
    stackoverflow_oauth_token = fields.CharField(
        max_length=50,
        null=True,
        description="Stackoverflow OAuth2 access token of the user",
    )

    thanks: fields.ForeignKeyRelation[ThankModel]
    sent_thanks: fields.ForeignKeyRelation[ThankModel]

    class Meta:
        table = "users"
        table_description = "Represents all users"


class JokeModel(Model):
    id = fields.IntField(pk=True, description="Joke ID")

    setup = fields.CharField(max_length=150, description="Joke setup")
    end = fields.CharField(max_length=150, description="Joke end")
    tags = fields.JSONField(default=[], description="List of tags")

    accepted = fields.BooleanField(
        default=False, description="Whether the joke has been accepted in"
    )

    creator = fields.ForeignKeyField(
        model_name="main.UserModel",
        related_name="joke_submissions",
        description="User who submitted this Joke",
    )

    class Meta:
        table = "jokes"
        table_description = "User submitted jokes being collected"
