import nextcord
from nextcord.ext import commands
import sqlite3
import time

# Класс для кнопок "Прошел" и "Не прошел" (появляются после взятия на рассмотрение)
class ButtonPassFail(nextcord.ui.View):
    def __init__(self, forms_instance, target_member, clan_role_id):
        super().__init__(timeout=None)
        self.forms_instance = forms_instance
        self.target_member = target_member
        self.clan_role_id = clan_role_id

    @nextcord.ui.button(label="Прошел", style=nextcord.ButtonStyle.grey)
    async def passed(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        # Проверяем права
        required_role_id = 1419024003502313553 # Роль руководства/наборщика
        required_role = interaction.guild.get_role(required_role_id)
        
        if required_role and required_role in interaction.user.roles:
            # Пытаемся выдать роль
            try:
                clan_role = interaction.guild.get_role(self.clan_role_id)
                if clan_role:
                    # Проверяем, может ли бот выдавать эту роль
                    if interaction.guild.me.guild_permissions.manage_roles and clan_role < interaction.guild.me.top_role:
                        await self.target_member.add_roles(clan_role)
                    else:
                        await interaction.response.send_message("❌ У бота нет прав для выдачи этой роли!", ephemeral=True)
                        return
            except nextcord.Forbidden:
                await interaction.response.send_message("❌ У бота недостаточно прав для выдачи роли!", ephemeral=True)
                return
            except Exception as e:
                await interaction.response.send_message(f"❌ Произошла ошибка: {e}", ephemeral=True)
                return
            
            # Уведомляем пользователя
            emb_success = nextcord.Embed(title="Поздравляем!", color=0x00ff00)
            emb_success.add_field(name="", value=f"* Привет! {self.target_member.mention}, вы успешно прошли проверку и приняты в клан на Christians!", inline=False)
            try:
                await self.target_member.send(embed=emb_success)
            except:
                pass  # Если ЛС закрыты
            
            # Обновляем сообщение о заявке
            embed = interaction.message.embeds[0]
            embed.set_field_at(1, name="", value=f"* ✅ Прошел проверку ({interaction.user.mention})", inline=False)
            await interaction.message.edit(embed=embed, view=None)
            
            await interaction.response.send_message("Пользователь успешно принят в клан!", ephemeral=True)
        else:
            await interaction.response.send_message("У вас недостаточно прав для выполнения этого действия.", ephemeral=True)

    @nextcord.ui.button(label="Не прошел", style=nextcord.ButtonStyle.grey)
    async def failed(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        # Проверяем права
        required_role_id = 1419024003502313553 # Роль руководства/наборщика
        required_role = interaction.guild.get_role(required_role_id)
        
        if required_role and required_role in interaction.user.roles:
            # Уведомляем пользователя
            emb_fail = nextcord.Embed(title="Уведомление от набора", color=0xff0000)
            emb_fail.add_field(name="", value=f"* Привет! {self.target_member.mention}, к сожалению, вы не прошли проверку в клан на Christians.", inline=False)
            try:
                await self.target_member.send(embed=emb_fail)
            except:
                pass  # Если ЛС закрыты
            
            # Обновляем сообщение о заявки
            embed = interaction.message.embeds[0]
            embed.set_field_at(1, name="", value=f"* ❌ Не прошел проверку ({interaction.user.mention})", inline=False)
            await interaction.message.edit(embed=embed, view=None)
            
            await interaction.response.send_message("Пользователь не прошел проверку.", ephemeral=True)
        else:
            await interaction.response.send_message("У вас недостаточно прав для выполнения этого действия.", ephemeral=True)

# Класс модального окна для заявки
class ModalView(nextcord.ui.Modal):
    def __init__(self, forms_instance):
        super().__init__("Набор на Christians")
        self.forms_instance = forms_instance
        self.spOne = nextcord.ui.TextInput(
            label="Ваше имя", placeholder="Ваш вариант", min_length=1, max_length=50)
        self.add_item(self.spOne)

        self.spTwo = nextcord.ui.TextInput(
            label="Ваш возраст", placeholder="Ваш вариант", min_length=1, max_length=50)
        self.add_item(self.spTwo)

        self.spFour = nextcord.ui.TextInput(
            label="Как вы оцениваете свои умения?", placeholder="Ваш вариант", min_length=1, max_length=50)
        self.add_item(self.spFour)

        self.spThree = nextcord.ui.TextInput(
            label="На каких серверах вы раньше стояли?",
            placeholder="Ваш вариант",
            min_length=1,
            max_length=50
        )
        self.add_item(self.spThree)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        if not await self.forms_instance.can_apply(interaction.user.id):
            await interaction.response.send_message("Вы не можете подать заявку снова в течение 24 часов после отклонения предыдущей.", ephemeral=True)
            return
        
        # Сохраняем данные заявки
        application_data = {
            "user": interaction.user,
            "spOne": self.spOne,
            "spTwo": self.spTwo,
            "spFour": self.spFour,
            "spThree": self.spThree
        }
        
        # Отправляем заявку в канал
        embed = nextcord.Embed(title="Заявка на Christians", color=0x808080)
        embed.add_field(name="", value=f"* Пользователь: {interaction.user.mention} ({interaction.user.id})", inline=False)
        embed.add_field(name="", value=f"* 📝 На рассмотрении", inline=False)
        embed.add_field(name=f"{self.spOne.label}", value=f"```{self.spOne.value}```", inline=False)
        embed.add_field(name="", value=f"", inline=False)
        embed.add_field(name=f"{self.spTwo.label}", value=f"```{self.spTwo.value}```", inline=False)
        embed.add_field(name="", value=f"", inline=False)
        embed.add_field(name=f"{self.spFour.label}", value=f"```{self.spFour.value}```", inline=False)
        embed.add_field(name="", value=f"", inline=False)
        embed.add_field(name=f"{self.spThree.label}", value=f"```{self.spThree.value}```", inline=False)
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        
        view = ApplicationButtons(self.forms_instance, application_data)
        await self.forms_instance.channel.send(embed=embed, view=view)
        await interaction.response.send_message("Ваша заявка отправлена на рассмотрение!", ephemeral=True)

# Класс для кнопок управления заявкой (Взять на рассмотрение/Отклонить)
class ApplicationButtons(nextcord.ui.View):
    def __init__(self, forms_instance, application_data):
        super().__init__(timeout=None)
        self.forms_instance = forms_instance
        self.application_data = application_data

    @nextcord.ui.button(label="Взять на рассмотрение", style=nextcord.ButtonStyle.grey)
    async def take_for_review(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        # Проверяем права
        required_role_id = 1419024003502313553
        required_role = interaction.guild.get_role(required_role_id)
        
        if required_role and required_role in interaction.user.roles:
            # Уведомляем пользователя
            emb_review = nextcord.Embed(title="Ваша заявка взята на рассмотрение", color=0x808080)
            emb_review.add_field(name="", value=f"* Привет! {self.application_data['user'].mention}, ваша заявка взята на рассмотрение. Ожидайте решения.", inline=False)
            try:
                await self.application_data['user'].send(embed=emb_review)
            except:
                pass  # Если ЛС закрыты
            
            # Обновляем сообщение о заявке
            embed = interaction.message.embeds[0]
            embed.set_field_at(1, name="", value=f"* 🔍 На проверке ({interaction.user.mention})", inline=False)
            
            # Заменяем кнопки на "Прошел/Не прошел"
            review_view = ButtonPassFail(
                self.forms_instance, 
                self.application_data['user'], 
                1419023974351896746  # ID роли клана
            )
            await interaction.message.edit(embed=embed, view=review_view)
            await interaction.response.send_message("Заявка взята на рассмотрение!", ephemeral=True)
        else:
            await interaction.response.send_message("У вас недостаточно прав для выполнения этого действия.", ephemeral=True)

    @nextcord.ui.button(label="Отклонить", style=nextcord.ButtonStyle.grey)
    async def reject(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        # Проверяем права
        required_role_id = 1419024003502313553
        required_role = interaction.guild.get_role(required_role_id)
        
        if required_role and required_role in interaction.user.roles:
            # Уведомляем пользователя
            emb_reject = nextcord.Embed(title="Уведомление от набора", color=0x808080)
            emb_reject.add_field(name="", value=f"* Привет! {self.application_data['user'].mention}, ваша заявка отклонена.", inline=False)
            try:
                await self.application_data['user'].send(embed=emb_reject)
            except:
                pass  # Если ЛС закрыты
            
            # Обновляем сообщение о заявке
            embed = interaction.message.embeds[0]
            embed.set_field_at(1, name="", value=f"* ❌ Отклонено ({interaction.user.mention})", inline=False)
            await interaction.message.edit(embed=embed, view=None)
            
            # Записываем время отклонения
            current_time = int(time.time())
            self.forms_instance.c.execute("INSERT OR REPLACE INTO applications (user_id, status, rejection_time) VALUES (?, ?, ?)", 
                                         (self.application_data['user'].id, "Rejected", current_time))
            self.forms_instance.conn.commit()
            
            await interaction.response.send_message("Заявка отклонена!", ephemeral=True)
        else:
            await interaction.response.send_message("У вас недостаточно прав для выполнения этого действия.", ephemeral=True)

# Класс для кнопки подачи заявки
class ApplyButton(nextcord.ui.View):
    def __init__(self, forms_instance):
        super().__init__(timeout=None)
        self.forms_instance = forms_instance

    @nextcord.ui.button(label="Подать Заявку", style=nextcord.ButtonStyle.grey)
    async def apply(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if not await self.forms_instance.can_apply(interaction.user.id):
            await interaction.response.send_message("Вы не можете подать заявку снова в течение 24 часов после отклонения предыдущей.", ephemeral=True)
            return
        modal = ModalView(self.forms_instance)
        await interaction.response.send_modal(modal)

# Основной ког Forms
class Forms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('applications.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS applications
                         (user_id INTEGER PRIMARY KEY, status TEXT, rejection_time INTEGER)''')
        self.conn.commit()
        self.channel = None

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Модуль заявок загружен")
        destination_guild = self.bot.get_guild(1418891695705034874)
        self.channel = destination_guild.get_channel(1418891696456073289)
        forms_channel = destination_guild.get_channel(1419024821177548880)
        
        # Очищаем предыдущие сообщения бота
        async for message in forms_channel.history(limit=10):
            if message.author.id == self.bot.user.id:
                await message.delete()
        
        # Отправляем новое сообщение с кнопкой
        embed = nextcord.Embed(description="**Набор на Christians**", color=0x808080)
        embed.add_field(name="Что нам от вас нужно:", value="・Нужно чтобы вам было от 14 лет\n・Адекватность", inline=False)
        embed.set_image(url="https://media.discordapp.net/attachments/1418317831195332748/1419021549159190528/ae777ff2-bb1d-4d1e-a516-d0ab57328dab.png?ex=68d03e4d&is=68ceeccd&hm=e6890c9f651e16e00809e1ab12581d8ba6892a6cef2baaf199e75517a27137a8&=&format=webp&quality=lossless&width=525&height=350")
        
        view = ApplyButton(self)
        await forms_channel.send(embed=embed, view=view)

    async def can_apply(self, user_id):
        current_time = int(time.time())
        self.c.execute("SELECT rejection_time FROM applications WHERE user_id=?", (user_id,))
        result = self.c.fetchone()
        if result:
            if current_time - result[0] < 86400:
                return False
        return True

    def cog_unload(self):
        self.conn.close()

def setup(bot):
    bot.add_cog(Forms(bot))