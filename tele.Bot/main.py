import os
import logging
import asyncio
import aiomysql
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)

# --- CONFIGURATION ---
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Please set the BOT_TOKEN environment variable.")

# --- ADMIN CONFIG ---
ADMIN_IDS = [
    int(admin_id.strip())
    for admin_id in os.getenv("ADMIN_IDS", "5070004661,153454360,1459499794").split(",")
    if admin_id.strip()
]

# --- DATABASE CONFIG ---
DB_CONFIG = {
    'host': os.getenv("DB_HOST", '127.0.0.1'),
    'port': int(os.getenv("DB_PORT", '3306')),
    'user': os.getenv("DB_USER", 'root'),
    'password': os.getenv("DB_PASS"),
    'db': os.getenv("DB_NAME", 'unimate_assitant_materials'),
    'autocommit': True
}

if not DB_CONFIG['password']:
    raise ValueError("Please set the DB_PASS environment variable.")

bot = Bot(token=TOKEN)
dp = Dispatcher()
temp_files = {}

# ================== COMMUNITY CONFIGURATION ==================
TEAMS = {
    "team_1": {
        "name": "Level 1",
        "icon": "👥",
        "whatsapp_link": "https://chat.whatsapp.com/Eig5BHV1atYKk3U3QKRNMj"
    },
    "team_2": {
        "name": "Level 2",
        "icon": "👥",
        "whatsapp_link": "https://chat.whatsapp.com/DsDLXrWB1whLwFixOrKtho"
    },
    "team_3": {
        "name": "Level 3",
        "icon": "👥",
        "whatsapp_link": "https://chat.whatsapp.com/KxCwwoxvMvg96Obhk5YVcO"
    },
    "team_4": {
        "name": "Level 4",
        "icon": "👥",
        "whatsapp_link": "https://chat.whatsapp.com/J8XwgpJxDsJ7t7HMnFUYjq"
    }
}

# ================== AUTO-INSERT HANDLERS (ADMIN ONLY) ==================

@dp.message(F.document, F.from_user.id.in_(ADMIN_IDS))
async def start_auto_insert(msg: Message):
    temp_files[msg.from_user.id] = msg.document.file_id
    buttons = [
        [InlineKeyboardButton(text="Year 1", callback_data="insyear_1")],
        [InlineKeyboardButton(text="Year 2", callback_data="insyear_2")],
        [InlineKeyboardButton(text="Year 3", callback_data="insyear_3")]
    ]
    await msg.reply("📥 **Auto-Insert Mode**\nSelect the Year for this file:", 
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("insyear_"), F.from_user.id.in_(ADMIN_IDS))
async def ins_choose_sem(call: CallbackQuery):
    year = call.data.split("_")[1]
    buttons = []
    for key in COURSE_MAP.keys():
        if key.startswith(year):
            buttons.append([InlineKeyboardButton(text=f"Semester/Part {key}", callback_data=f"inssem_{key}")])
    await call.message.edit_text("Select the Semester/Section:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("inssem_"), F.from_user.id.in_(ADMIN_IDS))
async def ins_choose_course(call: CallbackQuery):
    _, sem_key = call.data.split("_", 1) 
    courses = COURSE_MAP.get(sem_key, {})
    buttons = []
    for cid, name in courses.items():
        buttons.append([InlineKeyboardButton(text=name, callback_data=f"inscourse_{cid}")])
    await call.message.edit_text("Select the Course:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("inscourse_"), F.from_user.id.in_(ADMIN_IDS))
async def ins_choose_type(call: CallbackQuery):
    _, cid = call.data.split("_", 1)
    buttons = [
        [InlineKeyboardButton(text="📝 Lecture", callback_data=f"instype_{cid}_lec")],
        [InlineKeyboardButton(text="🗣️ Practical", callback_data=f"instype_{cid}_prac")],
        [InlineKeyboardButton(text="❓ Question", callback_data=f"instype_{cid}_q")]
    ]
    await call.message.edit_text("Select Category:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("instype_"), F.from_user.id.in_(ADMIN_IDS))
async def ins_choose_part(call: CallbackQuery):
    _, cid, m_type = call.data.split("_")
    
    is_level_3 = any(cid in COURSE_MAP[k] for k in ["3_1", "3_2", "3_3", "3_4", "3_5"])
    
    if is_level_3:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor() as cur:
            await cur.execute("SELECT MAX(CAST(part_number AS UNSIGNED)) FROM materials WHERE course_id=%s AND material_type=%s", (cid, m_type))
            res = await cur.fetchone()
            next_part = (res[0] or 0) + 1
        conn.close()
        await final_save_to_db(call, cid, m_type, str(next_part))
    else:
        buttons = []
        for i in range(1, 13, 3):
            row = [
                InlineKeyboardButton(text=str(i), callback_data=f"inssave_{cid}_{m_type}_{i}"),
                InlineKeyboardButton(text=str(i+1), callback_data=f"inssave_{cid}_{m_type}_{i+1}"),
                InlineKeyboardButton(text=str(i+2), callback_data=f"inssave_{cid}_{m_type}_{i+2}")
            ]
            buttons.append(row)
        await call.message.edit_text("Select Part Number (1-12) to SAVE:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("inssave_"), F.from_user.id.in_(ADMIN_IDS))
async def final_save_callback(call: CallbackQuery):
    _, cid, m_type, part = call.data.split("_")
    await final_save_to_db(call, cid, m_type, part)

async def final_save_to_db(call: CallbackQuery, cid, m_type, part):
    file_id = temp_files.get(call.from_user.id)
    if not file_id:
        return await call.message.edit_text("❌ Session expired. Send the file again.")
    
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor() as cur:
            sql = """INSERT INTO materials (course_id, material_type, part_number, file_id) 
                     VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE file_id = %s"""
            await cur.execute(sql, (cid, m_type, part, file_id, file_id))
            await conn.commit()
        conn.close()
        if call.from_user.id in temp_files:
            del temp_files[call.from_user.id]
        await call.message.edit_text(f"✅ **Success!**\nSaved `{cid}` as File #{part}.")
    except Exception as e:
        logging.error(f"Database error: {e}")
        await call.message.edit_text(f"❌ **Database Error:**\n{str(e)}")

# ================== COURSE DATABASE ==================
COURSE_MAP = {
    "1_1": {"dm1": "Discrete Mathematics", "tw1": "Technical Writing", "ct1": "Creative Thinking", "sp1": "Structure Programing", "el1": "Electronic", "pm1": "Project Management", "ca1": "Calculus", "ql1": "الجودة"},
    "1_2": {"ld2": "Logic Design", "oo2": "OOP", "st2": "Statistics", "la2": "Linear Algebra", "em2": "Electromagnetic", "m22": "Math 2", "sc2": "القضايا المجتمعية"},
    "2_1": {"ds3": "Data Structure", "ai3": "Artificial intelligence", "dsp3": "Digital signal Processing", "sw3": "Software", "dsc3": "Data Science", "m33": "Math 3"},
    "2_2": {"nw4": "Network", "db4": "Database", "da4": "Data Analysis", "ml4": "Machine learning", "os4": "Operating system", "dip4": "Digital Image Processing"},
    "3_1": {"dl5": "Deep learning", "au5": "Intro to automata", "ro5": "Introduction to Robotics", "cv5": "Computer Vision", "lp5": "Logic programming", "cs5": "Cyber Security Fundamental"},
    "3_2": {"aml6": "Applied machine learning", "dsc6": "Data science", "bd6": "Big data", "nlp6": "NLP", "rl6": "Reinforcement learning", "sw26": "Software 2"}, 
    "3_3": {"cog7": "Cognitive Science", "dsp7": "Digital Signal processing", "fp7": "FPGA Design", "iot7": "IoT", "nn7": "Neural networks", "per7": "Perception"}, 
    "3_4": {"is8": "Info._Security", "sda8": "Sw_Development_Analyses", "ms8": "Multimedia_Security", "ws8": "Security_web", "cr8": "Intro_to_Cryptography", "cws8": "Cellular_Wireless_Security"}, 
    "3_5": {"aml9": "Applied machine learning", "dsc9": "Data science", "bd9": "Big data", "nlp9": "NLP", "rl9": "Reinforcement learning", "cry9": "Crypto"}  
}

# ================== Keyboards & Public Handlers ==================
def get_main_kb():
    buttons = [
        [InlineKeyboardButton(text="📚 Level 1", callback_data="year_1"),
         InlineKeyboardButton(text="📚 Level 2", callback_data="year_2")],
        [InlineKeyboardButton(text="📚 Level 3", callback_data="year_3")], 
        [InlineKeyboardButton(text="🤝 Join Community", callback_data="action_join_community"),
         InlineKeyboardButton(text="💡 Give Suggestion", url="https://forms.gle/uMwhAgYkTo1wjuJy9")],
        [InlineKeyboardButton(text="📂 External Resources", url="https://drive.google.com/drive/folders/1xkwyOLrdfsq72X92cC8G8OLDqyX3gtfZ?usp=sharing")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_teams_kb():
    buttons = [
        [InlineKeyboardButton(
            text=f"{team['icon']} {team['name']}",
            callback_data=f"team_{team_id}"
        )]
        for team_id, team in TEAMS.items()
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_team_community_kb(team_id: str, team: dict):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"💬 Join {team['name']} WhatsApp Community",
            url=team["whatsapp_link"]
        )],
        [InlineKeyboardButton(text="🔙 Back", callback_data="action_join_community")]
    ])

def get_semester_kb(year: str):
    buttons = [
        [InlineKeyboardButton(text="1️⃣ First Semester", callback_data=f"sem_{year}_1")],
        [InlineKeyboardButton(text="2️⃣ Second Semester", callback_data=f"sem_{year}_split" if year == "3" else f"sem_{year}_2")],
        [InlineKeyboardButton(text="⬅️ Back to Levels", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_l3_parts_kb():
    buttons = [
        [InlineKeyboardButton(text="📦 MI", callback_data="sem_3_2"),
         InlineKeyboardButton(text="📦 IS", callback_data="sem_3_3")],
        [InlineKeyboardButton(text="📦 CY", callback_data="sem_3_4"),
         InlineKeyboardButton(text="📦 DS", callback_data="sem_3_5")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="year_3")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_content_kb(year: str, sem: str):
    key = f"{year}_{sem}"
    courses = COURSE_MAP.get(key, {})
    buttons = []
    ids = list(courses.keys())
    for i in range(0, len(ids), 2):
        cid1 = ids[i]
        row = [InlineKeyboardButton(text=f"📘 {courses[cid1]}", callback_data=f"type_{year}_{sem}_{cid1}")]
        if i + 1 < len(ids):
            cid2 = ids[i+1]
            row.append(InlineKeyboardButton(text=f"📘 {courses[cid2]}", callback_data=f"type_{year}_{sem}_{cid2}"))
        buttons.append(row)
    back_target = "l3_split" if (year == "3" and sem in ["2", "3", "4", "5"]) else f"year_{year}"
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data=back_target)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def cmd_start(msg: Message):
    await msg.answer(f"👋 Welcome {msg.from_user.first_name}!\nSelect level:", reply_markup=get_main_kb())

@dp.callback_query(F.data == "action_join_community")
async def show_teams(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text("👥 Please select your Level:", reply_markup=get_teams_kb())

@dp.callback_query(F.data.startswith("team_"))
async def show_team_community(call: CallbackQuery):
    team_id = call.data.removeprefix("team_")
    team = TEAMS.get(team_id)
    if not team or not team.get("whatsapp_link"):
        await call.answer("⚠️ This level is unavailable.", show_alert=True)
        return

    await call.answer()
    await call.message.edit_text(
        f"🎉 {team['name']} Community\n\n"
        "Join your WhatsApp community using the button below 👇",
        reply_markup=get_team_community_kb(team_id, team)
    )

@dp.callback_query(F.data.startswith("year_"))
async def show_semesters(call: CallbackQuery):
    year = call.data.split("_")[1]
    await call.message.edit_text(text=f"✨ Level {year}", reply_markup=get_semester_kb(year))

@dp.callback_query(F.data == "sem_3_split")
@dp.callback_query(F.data == "l3_split")
async def show_l3_parts(call: CallbackQuery):
    await call.message.edit_text(text="📂 Level 3 - Select Part:", reply_markup=get_l3_parts_kb())

@dp.callback_query(F.data.startswith("sem_"))
async def show_courses(call: CallbackQuery):
    _, year, sem = call.data.split("_")
    await call.message.edit_text(text=f"📅 Level {year}", reply_markup=get_content_kb(year, sem))

@dp.callback_query(F.data.startswith("type_"))
async def choose_material_type(call: CallbackQuery):
    _, year, sem, course_id = call.data.split("_")
    course_name = COURSE_MAP[f"{year}_{sem}"].get(course_id, "Unknown")
    buttons = [
        [InlineKeyboardButton(text="📝 Lectures", callback_data=f"list_{year}_{sem}_{course_id}_lec")],
        [InlineKeyboardButton(text="🗣️ Practical", callback_data=f"list_{year}_{sem}_{course_id}_prac")],
        [InlineKeyboardButton(text="❓ Questions", callback_data=f"list_{year}_{sem}_{course_id}_q")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data=f"sem_{year}_{sem}")]
    ]
    await call.message.edit_text(f"📂 *{course_name}*", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("list_"))
async def show_parts_grid(call: CallbackQuery):
    _, year, sem, course_id, m_type = call.data.split("_")
    
    if year == "3":
        try:
            conn = await aiomysql.connect(**DB_CONFIG)
            async with conn.cursor() as cur:
                await cur.execute("SELECT part_number FROM materials WHERE course_id=%s AND material_type=%s ORDER BY CAST(part_number AS UNSIGNED)", (course_id, m_type))
                results = await cur.fetchall()
            conn.close()
        except Exception as e:
            logging.error(f"Database error: {e}")
            return await call.answer("Database error occurred.", show_alert=True)

        if not results:
            return await call.answer("⚠️ Not uploaded yet!", show_alert=True)

        buttons = []
        for i in range(0, len(results), 3):
            row = []
            for r in results[i:i+3]:
                p_num = r[0]
                row.append(InlineKeyboardButton(text=f"File {p_num}", callback_data=f"files_{course_id}_{m_type}_{p_num}"))
            buttons.append(row)
        
        buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data=f"type_{year}_{sem}_{course_id}")])
        await call.message.edit_text(text="Select a file to download:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    
    else:
        buttons = []
        for i in range(1, 13, 3):
            row = [
                InlineKeyboardButton(text=f"{i}", callback_data=f"files_{course_id}_{m_type}_{i}"),
                InlineKeyboardButton(text=f"{i+1}", callback_data=f"files_{course_id}_{m_type}_{i+1}"),
                InlineKeyboardButton(text=f"{i+2}", callback_data=f"files_{course_id}_{m_type}_{i+2}")
            ]
            buttons.append(row)
        buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data=f"type_{year}_{sem}_{course_id}")])
        await call.message.edit_text(text="Select Number (1-12):", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("files_"))
async def files_callback(call: CallbackQuery):
    data = call.data.split("_")
    await send_file_logic(call, data[1], data[2], data[3])

async def send_file_logic(call: CallbackQuery, course_id, m_type, part_num):
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor() as cur:
            query = "SELECT file_id FROM materials WHERE course_id=%s AND material_type=%s AND part_number=%s"
            await cur.execute(query, (course_id, m_type, part_num))
            result = await cur.fetchone()
        conn.close()
    except Exception as e:
        logging.error(f"Database error: {e}")
        return await call.answer("Database error occurred.", show_alert=True)

    if result:
        file_id = result[0]
        if file_id.startswith("http"):
            await call.message.answer(f"🔗 [Link]({file_id})", parse_mode="Markdown")
        else:
            await bot.send_document(call.from_user.id, file_id)
        await call.answer()
    else:
        await call.answer(f"⚠️ File not found!", show_alert=True)

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(call: CallbackQuery):
    await call.message.edit_text("📚 Select your academic year:", reply_markup=get_main_kb())

async def main():
    logging.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())