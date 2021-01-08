from tortoise import Model, fields


class ThankModel(Model):
    id = fields.IntField(pk=True)
    thanker = fields.ForeignKeyField(
        model_name="main.MemberModel",
        related_name="sent_thanks",
        description="The member who sent the thanks")
    thanked = fields.ForeignKeyField(
        model_name="main.MemberModel",
        related_name="thanks",
        description="The member who was thanked for the help")
    time = fields.DatetimeField(auto_now_add=True)
    description = fields.CharField(max_length=100)

    class Meta:
        table = "thanks"
        table_description = "Represents a 'thank' given from one member to another"


class BotModel(Model):
    # IDs
    id = fields.BigIntField(pk=True, description="Discord ID of the bot")
    client_id = fields.BigIntField()
    # Decision
    decision = fields.BooleanField(null=True)
    # Description
    for_testing = fields.BooleanField(
        default=True,
        description="Whether the bot has been added by a user for testing")
    description = fields.CharField(
        max_length=200, description="Description of the bot")
    # Ownership
    user_owner = fields.ForeignKeyField(
        model_name="main.MemberModel",
        null=True,
        related_name="owned_bots",
        description="Owner of the bot")
    dev_team = fields.ForeignKeyField(
        model_name="main.TeamModel",
        null=True,
        related_name="owned_bots",
        description="The team that develops the bot")

    class Meta:
        table = "bots"
        table_description = "Represents all bots in the server"


class TeamModel(Model):
    id = fields.IntField(pk=True)
    admins = fields.ManyToManyField(
        model_name="main.MemberModel",
        related_name="administratored_teams",
        description="Admins of the team")
    members = fields.ManyToManyField(
        model_name="main.MemberModel",
        related_name="teams",
        description="All members of the team")

    owned_bots: fields.ForeignKeyRelation[BotModel]

    class Meta:
        table = "teams"
        table_description = "Represents a team of developers"


class MemberModel(Model):
    id = fields.BigIntField(
        pk=True, description="Discord ID of the member joined")
    # External references
    github_username = fields.CharField(
        max_length=30, null=True, description="Github username of the member")
    stackoverflow_id = fields.BigIntField(
        null=True, description="Stackoverflow ID of the user")

    thanks: fields.ForeignKeyRelation[ThankModel]
    sent_thanks: fields.ForeignKeyRelation[ThankModel]
    owned_bots: fields.ForeignKeyRelation[BotModel]
    teams: fields.ManyToManyRelation[TeamModel]
    administratored_teams: fields.ManyToManyRelation[TeamModel]

    class Meta:
        table = "members"
        table_description = "Represents all members"
