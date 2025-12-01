# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[7.0].define(version: 2025_11_30_000000) do
  # These are extensions that must be enabled in order to support this database
  enable_extension "plpgsql"

  create_table "chat_rooms", force: :cascade do |t|
    t.string "name"
    t.integer "creator_id", null: false
    t.datetime "created_at", null: false
    t.boolean "is_active", default: true, null: false
    t.string "room_type", default: "group", null: false
    t.boolean "ai_enabled", default: true, null: false
    t.string "password"
    t.boolean "is_public", default: false, null: false
    t.index ["creator_id"], name: "index_chat_rooms_on_creator_id"
    t.index ["id"], name: "index_chat_rooms_on_id"
  end

  create_table "error_logs", force: :cascade do |t|
    t.datetime "timestamp", default: -> { "CURRENT_TIMESTAMP" }
    t.integer "user_id"
    t.string "error_type", limit: 100, null: false
    t.text "error_message", null: false
    t.text "stack_trace"
    t.json "context"
    t.index ["id"], name: "index_error_logs_on_id"
    t.index ["user_id"], name: "index_error_logs_on_user_id"
  end

  create_table "general_chat_messages", force: :cascade do |t|
    t.integer "sender_id", null: false
    t.text "content", null: false
    t.datetime "created_at", null: false
    t.index ["created_at"], name: "index_general_chat_messages_on_created_at"
    t.index ["id"], name: "index_general_chat_messages_on_id"
    t.index ["sender_id"], name: "index_general_chat_messages_on_sender_id"
  end

  create_table "room_invites", force: :cascade do |t|
    t.integer "room_id", null: false
    t.integer "inviter_id", null: false
    t.integer "invitee_id", null: false
    t.string "status", default: "pending", null: false
    t.integer "message_id"
    t.datetime "created_at", null: false
    t.datetime "responded_at"
    t.index ["id"], name: "index_room_invites_on_id"
    t.index ["invitee_id"], name: "index_room_invites_on_invitee_id"
    t.index ["inviter_id"], name: "index_room_invites_on_inviter_id"
    t.index ["message_id"], name: "index_room_invites_on_message_id"
    t.index ["room_id", "invitee_id"], name: "index_room_invites_on_room_id_and_invitee_id", unique: true
    t.index ["room_id"], name: "index_room_invites_on_room_id"
  end

  create_table "room_members", force: :cascade do |t|
    t.integer "room_id", null: false
    t.integer "user_id"
    t.datetime "joined_at", null: false
    t.string "role", default: "member", null: false
    t.boolean "is_active", default: true, null: false
    t.datetime "last_read_at"
    t.index ["id"], name: "index_room_members_on_id"
    t.index ["room_id", "user_id"], name: "index_room_members_on_room_id_and_user_id", unique: true
    t.index ["room_id"], name: "index_room_members_on_room_id"
    t.index ["user_id"], name: "index_room_members_on_user_id"
  end

  create_table "room_messages", force: :cascade do |t|
    t.integer "room_id", null: false
    t.integer "sender_id"
    t.string "sender_type", default: "user", null: false
    t.text "content", null: false
    t.string "message_type", default: "text", null: false
    t.json "message_metadata"
    t.datetime "created_at", null: false
    t.datetime "edited_at"
    t.boolean "is_deleted", default: false, null: false
    t.index ["created_at"], name: "index_room_messages_on_created_at"
    t.index ["id"], name: "index_room_messages_on_id"
    t.index ["room_id"], name: "index_room_messages_on_room_id"
    t.index ["sender_id"], name: "index_room_messages_on_sender_id"
  end

  create_table "skills", force: :cascade do |t|
    t.string "skill_name"
    t.index ["id"], name: "index_skills_on_id"
    t.index ["skill_name"], name: "index_skills_on_skill_name", unique: true
  end

  create_table "token_blacklist", force: :cascade do |t|
    t.string "token", null: false
    t.datetime "expires_at", null: false
    t.datetime "created_at", default: -> { "CURRENT_TIMESTAMP" }, null: false
    t.integer "user_id"
    t.string "reason"
    t.index ["id"], name: "index_token_blacklist_on_id"
    t.index ["token"], name: "index_token_blacklist_on_token", unique: true
    t.index ["user_id"], name: "index_token_blacklist_on_user_id"
  end

  create_table "training", primary_key: ["user_id", "skill_id"], force: :cascade do |t|
    t.integer "user_id", null: false
    t.integer "skill_id", null: false
    t.string "status", default: "pending"
    t.float "progress", default: 0.0
    t.date "started_at", default: -> { "CURRENT_DATE" }
    t.date "completed_at"
    t.string "notes"
    t.index ["skill_id"], name: "index_training_on_skill_id"
    t.index ["user_id", "skill_id"], name: "index_training_on_user_id_and_skill_id"
    t.index ["user_id"], name: "index_training_on_user_id"
  end

  create_table "user_preferences", force: :cascade do |t|
    t.integer "user_id", null: false
    t.string "preference_type", null: false
    t.string "preference_key", null: false
    t.json "preference_value", null: false
    t.float "confidence", default: 1.0
    t.date "last_updated", default: -> { "CURRENT_DATE" }
    t.index ["id"], name: "index_user_preferences_on_id"
    t.index ["user_id", "preference_type", "preference_key"], name: "idx_user_pref_unique", unique: true
    t.index ["user_id"], name: "index_user_preferences_on_user_id"
  end

  create_table "user_skills", force: :cascade do |t|
    t.integer "user_id", null: false
    t.integer "skill_id", null: false
    t.integer "level", default: 0
    t.index ["skill_id"], name: "index_user_skills_on_skill_id"
    t.index ["user_id", "skill_id"], name: "index_user_skills_on_user_id_and_skill_id", unique: true
    t.index ["user_id"], name: "index_user_skills_on_user_id"
  end

  create_table "users", force: :cascade do |t|
    t.string "username", null: false
    t.string "role", default: "user"
    t.boolean "is_active", default: true, null: false
    t.float "temperature", default: 0.7
    t.json "preferences", default: {}
    t.string "hashed_name", default: ""
    t.string "hashed_password", null: false
    t.string "hashed_email", null: false
    t.date "member_since", default: -> { "CURRENT_DATE" }
    t.integer "messages", default: 0
    t.string "encryption_key"
    t.text "conversation_memory"
    t.string "llm_provider"
    t.string "llm_endpoint"
    t.string "llm_model"
    t.index ["hashed_email"], name: "index_users_on_hashed_email", unique: true
    t.index ["id"], name: "index_users_on_id"
    t.index ["username"], name: "index_users_on_username", unique: true
  end

  add_foreign_key "chat_rooms", "users", column: "creator_id", on_delete: :cascade
  add_foreign_key "error_logs", "users", on_delete: :cascade
  add_foreign_key "general_chat_messages", "users", column: "sender_id", on_delete: :cascade
  add_foreign_key "room_invites", "chat_rooms", column: "room_id", on_delete: :cascade
  add_foreign_key "room_invites", "room_messages", column: "message_id", on_delete: :nullify
  add_foreign_key "room_invites", "users", column: "invitee_id", on_delete: :cascade
  add_foreign_key "room_invites", "users", column: "inviter_id", on_delete: :cascade
  add_foreign_key "room_members", "chat_rooms", column: "room_id", on_delete: :cascade
  add_foreign_key "room_members", "users", on_delete: :cascade
  add_foreign_key "room_messages", "chat_rooms", column: "room_id", on_delete: :cascade
  add_foreign_key "room_messages", "users", column: "sender_id", on_delete: :nullify
  add_foreign_key "token_blacklist", "users", on_delete: :cascade
  add_foreign_key "training", "skills", on_delete: :cascade
  add_foreign_key "training", "users", on_delete: :cascade
  add_foreign_key "user_preferences", "users", on_delete: :cascade
  add_foreign_key "user_skills", "skills", on_delete: :cascade
  add_foreign_key "user_skills", "users", on_delete: :cascade
end
