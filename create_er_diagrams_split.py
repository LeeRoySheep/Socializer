#!/usr/bin/env python3
"""
Generate TWO separate ER diagrams matching the original structure:
1. Left diagram: Core + Room Management + Skills
2. Right diagram: User Data + System tables

Cross-diagram relationships get UNIQUE COLORS (same color in both diagrams).
"""

import sqlite3
from graphviz import Digraph


# Define color palette for cross-diagram relationships
CROSS_COLORS = [
    '#FF0000',  # Red
    '#0000FF',  # Blue
    '#00FF00',  # Green
    '#FF00FF',  # Magenta
    '#FFA500',  # Orange
    '#00FFFF',  # Cyan
    '#FF1493',  # Deep Pink
    '#8B00FF',  # Violet
    '#FFD700',  # Gold
    '#00CED1',  # Dark Turquoise
    '#FF4500',  # Orange Red
    '#9400D3',  # Dark Violet
    '#32CD32',  # Lime Green
    '#FF69B4',  # Hot Pink
    '#1E90FF',  # Dodger Blue
]


def get_database_schema(db_path='data/socializer.db'):
    """Extract database schema from SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]
    
    schema = {}
    
    for table in tables:
        # Get table info
        cursor.execute(f"PRAGMA table_info({table});")
        columns_info = cursor.fetchall()
        
        columns = []
        primary_keys = []
        
        for col in columns_info:
            col_name = col[1]
            col_type = col[2]
            is_pk = col[5]
            
            columns.append({
                'name': col_name,
                'type': col_type,
                'primary_key': bool(is_pk)
            })
            
            if is_pk:
                primary_keys.append(col_name)
        
        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table});")
        foreign_keys_info = cursor.fetchall()
        
        foreign_keys = []
        for fk in foreign_keys_info:
            foreign_keys.append({
                'column': fk[3],
                'references_table': fk[2],
                'references_column': fk[4]
            })
        
        schema[table] = {
            'columns': columns,
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys
        }
    
    conn.close()
    return schema


def create_placeholder_table(table_name):
    """Create placeholder for tables that don't exist yet."""
    return {
        'columns': [
            {'name': 'id', 'type': 'INTEGER', 'primary_key': True},
            {'name': 'created_at', 'type': 'TIMESTAMP', 'primary_key': False},
            {'name': '...', 'type': 'PLANNED', 'primary_key': False},
        ],
        'primary_keys': ['id'],
        'foreign_keys': []
    }


def create_table_node(graph, table_name, table_info, is_placeholder=False):
    """Create an HTML table node for a database table."""
    
    # Different styling for placeholder tables
    title_bg = '#95a5a6' if is_placeholder else '#3498db'
    
    # Start HTML table
    html = f'''<
        <TABLE BORDER="2" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">
            <TR>
                <TD BGCOLOR="{title_bg}" COLSPAN="2">
                    <FONT COLOR="white" POINT-SIZE="14"><B>{table_name.upper()}</B></FONT>
                </TD>
            </TR>
    '''
    
    if is_placeholder:
        html += '''
            <TR>
                <TD COLSPAN="2" ALIGN="CENTER" BGCOLOR="#ffffcc">
                    <FONT POINT-SIZE="10" COLOR="#666666"><I>⚠️ Planned</I></FONT>
                </TD>
            </TR>
        '''
    
    # Add columns - show up to 8 columns
    for col in table_info['columns'][:8]:
        icon = '🔑' if col['primary_key'] else '•'
        col_type = col['type'] if col['type'] else 'TEXT'
        
        # Color code by type
        if col['primary_key']:
            bgcolor = '#e8f4f8'
        elif 'password' in col['name'].lower() or 'encryption' in col['name'].lower():
            bgcolor = '#ffe8e8'
        else:
            bgcolor = 'white'
        
        html += f'''
            <TR>
                <TD ALIGN="LEFT" BGCOLOR="{bgcolor}">
                    <FONT POINT-SIZE="10">{icon} {col['name']}</FONT>
                </TD>
                <TD ALIGN="LEFT" BGCOLOR="{bgcolor}">
                    <FONT POINT-SIZE="9" COLOR="#7f8c8d">{col_type}</FONT>
                </TD>
            </TR>
        '''
    
    # Add ellipsis if more columns
    if len(table_info['columns']) > 8:
        html += '''
            <TR>
                <TD COLSPAN="2" ALIGN="CENTER">
                    <FONT POINT-SIZE="10" COLOR="#95a5a6">...</FONT>
                </TD>
            </TR>
        '''
    
    html += '    </TABLE>\n>'
    
    graph.node(table_name, label=html)


def identify_cross_relationships(schema, left_tables, right_tables):
    """Identify all relationships that cross between diagrams and assign colors."""
    cross_relations = []
    
    # Check relationships from left to right
    for table in left_tables:
        if table not in schema:
            continue
        for fk in schema[table]['foreign_keys']:
            if fk['references_table'] in right_tables:
                cross_relations.append({
                    'from': table,
                    'to': fk['references_table'],
                    'column': fk['column'],
                    'ref_column': fk['references_column']
                })
    
    # Check relationships from right to left
    for table in right_tables:
        if table not in schema:
            continue
        for fk in schema[table]['foreign_keys']:
            if fk['references_table'] in left_tables:
                cross_relations.append({
                    'from': table,
                    'to': fk['references_table'],
                    'column': fk['column'],
                    'ref_column': fk['references_column']
                })
    
    # Assign unique colors
    color_map = {}
    for i, rel in enumerate(cross_relations):
        key = f"{rel['from']}->{rel['to']}:{rel['column']}"
        color_map[key] = CROSS_COLORS[i % len(CROSS_COLORS)]
    
    return color_map


def create_left_diagram(schema, color_map, output_filename='socializer_er_left'):
    """Create left ER diagram: Core + Room Management + Skills."""
    
    dot = Digraph(comment='Socializer Left ER Diagram')
    dot.attr(rankdir='TB', splines='ortho', nodesep='0.5', ranksep='1.2')
    dot.attr('node', shape='plaintext', fontname='Arial')
    dot.attr('graph', bgcolor='white', dpi='300')
    
    # Define tables for LEFT diagram (based on images)
    core_tables = ['users']
    room_tables = ['chat_rooms', 'messages', 'room_members', 'room_messages', 'room_invites', 'general_chat_messages']
    skill_tables = ['skills']
    
    left_tables = core_tables + room_tables + skill_tables
    right_tables = ['user_skills', 'user_preferences', 'training', 'life_events', 'error_logs', 'token_blacklist']
    
    # ROW 1: Core table
    with dot.subgraph(name='cluster_core') as c:
        c.attr(label='Core Tables', fontsize='20', fontname='Arial Bold')
        c.attr(style='dashed', color='#2980b9')
        
        for table_name in core_tables:
            if table_name in schema:
                create_table_node(c, table_name, schema[table_name], is_placeholder=False)
            else:
                create_table_node(c, table_name, create_placeholder_table(table_name), is_placeholder=True)
    
    # ROW 2: Room Management
    with dot.subgraph(name='cluster_rooms') as c:
        c.attr(label='Room Management', fontsize='20', fontname='Arial Bold')
        c.attr(style='dashed', color='#27ae60')
        c.attr(rank='same')
        
        for table_name in room_tables:
            if table_name in schema:
                create_table_node(c, table_name, schema[table_name], is_placeholder=False)
            else:
                create_table_node(c, table_name, create_placeholder_table(table_name), is_placeholder=True)
    
    # ROW 3: Skills
    with dot.subgraph(name='cluster_skills') as c:
        c.attr(label='Skills', fontsize='20', fontname='Arial Bold')
        c.attr(style='dashed', color='#3498db')
        
        for table_name in skill_tables:
            if table_name in schema:
                create_table_node(c, table_name, schema[table_name], is_placeholder=False)
            else:
                create_table_node(c, table_name, create_placeholder_table(table_name), is_placeholder=True)
    
    # Add relationships
    for table_name in left_tables:
        if table_name not in schema:
            continue
            
        for fk in schema[table_name]['foreign_keys']:
            ref_table = fk['references_table']
            key = f"{table_name}->{ref_table}:{fk['column']}"
            
            if ref_table in left_tables:
                # Internal relationship - normal gray
                dot.edge(
                    table_name,
                    ref_table,
                    label=f"{fk['column']}",
                    color='#34495e',
                    penwidth='2',
                    arrowhead='crow',
                    arrowtail='none'
                )
            elif ref_table in right_tables and key in color_map:
                # Cross-diagram relationship - use assigned color
                dot.edge(
                    table_name,
                    ref_table,
                    label=f"{fk['column']}",
                    color=color_map[key],
                    penwidth='4',
                    arrowhead='crow',
                    arrowtail='none',
                    style='solid'
                )
    
    # Render
    output_file = f'{output_filename}'
    dot.render(output_file, format='png', cleanup=True)
    
    print(f"✅ Left diagram created: {output_file}.png")
    return f"{output_file}.png"


def create_right_diagram(schema, color_map, output_filename='socializer_er_right'):
    """Create right ER diagram: User Data + System tables."""
    
    dot = Digraph(comment='Socializer Right ER Diagram')
    dot.attr(rankdir='TB', splines='ortho', nodesep='0.5', ranksep='1.2')
    dot.attr('node', shape='plaintext', fontname='Arial')
    dot.attr('graph', bgcolor='white', dpi='300')
    
    # Define tables for RIGHT diagram (based on images)
    user_tables = ['user_skills', 'user_preferences', 'training', 'life_events']
    system_tables = ['error_logs', 'token_blacklist']
    
    right_tables = user_tables + system_tables
    left_tables = ['users', 'chat_rooms', 'messages', 'room_members', 'room_messages', 
                   'room_invites', 'general_chat_messages', 'skills']
    
    # ROW 1: User data
    with dot.subgraph(name='cluster_users') as c:
        c.attr(label='User Data', fontsize='20', fontname='Arial Bold')
        c.attr(style='dashed', color='#e74c3c')
        
        for table_name in user_tables:
            if table_name in schema:
                create_table_node(c, table_name, schema[table_name], is_placeholder=False)
            else:
                create_table_node(c, table_name, create_placeholder_table(table_name), is_placeholder=True)
    
    # ROW 2: System tables
    with dot.subgraph(name='cluster_system') as c:
        c.attr(label='System Tables', fontsize='20', fontname='Arial Bold')
        c.attr(style='dashed', color='#95a5a6')
        c.attr(rank='same')
        
        for table_name in system_tables:
            if table_name in schema:
                create_table_node(c, table_name, schema[table_name], is_placeholder=False)
            else:
                create_table_node(c, table_name, create_placeholder_table(table_name), is_placeholder=True)
    
    # Add relationships
    for table_name in right_tables:
        if table_name not in schema:
            continue
            
        for fk in schema[table_name]['foreign_keys']:
            ref_table = fk['references_table']
            key = f"{table_name}->{ref_table}:{fk['column']}"
            
            if ref_table in right_tables:
                # Internal relationship - normal gray
                dot.edge(
                    table_name,
                    ref_table,
                    label=f"{fk['column']}",
                    color='#34495e',
                    penwidth='2',
                    arrowhead='crow',
                    arrowtail='none'
                )
            elif ref_table in left_tables and key in color_map:
                # Cross-diagram relationship - use assigned color
                dot.edge(
                    table_name,
                    ref_table,
                    label=f"{fk['column']}",
                    color=color_map[key],
                    penwidth='4',
                    arrowhead='crow',
                    arrowtail='none',
                    style='solid'
                )
    
    # Render
    output_file = f'{output_filename}'
    dot.render(output_file, format='png', cleanup=True)
    
    print(f"✅ Right diagram created: {output_file}.png")
    return f"{output_file}.png"


def main():
    """Generate both ER diagrams."""
    print("=" * 70)
    print("🎨 GENERATING SPLIT ER DIAGRAMS (LEFT/RIGHT)")
    print("=" * 70)
    print()
    
    # Extract schema
    print("📊 Extracting database schema...")
    schema = get_database_schema()
    print(f"   Found {len(schema)} existing tables")
    print()
    
    # Define table groups (based on images)
    left_tables = ['users', 'chat_rooms', 'messages', 'room_members', 'room_messages', 
                   'room_invites', 'general_chat_messages', 'skills']
    right_tables = ['user_skills', 'user_preferences', 'training', 'life_events',
                    'error_logs', 'token_blacklist']
    
    # Identify cross-diagram relationships and assign colors
    print("🎨 Identifying cross-diagram relationships...")
    color_map = identify_cross_relationships(schema, left_tables, right_tables)
    print(f"   Found {len(color_map)} cross-diagram relationships")
    print()
    
    # Print color assignments
    if color_map:
        print("🌈 Color assignments for cross-diagram relationships:")
        for key, color in color_map.items():
            parts = key.split('->')
            from_table = parts[0]
            rest = parts[1].split(':')
            to_table = rest[0]
            column = rest[1]
            print(f"   {color} : {from_table}.{column} → {to_table}")
        print()
    
    # Generate diagrams
    print("🎨 Creating diagrams...")
    print()
    
    left_file = create_left_diagram(schema, color_map)
    print()
    
    right_file = create_right_diagram(schema, color_map)
    print()
    
    print("=" * 70)
    print("✅ BOTH DIAGRAMS CREATED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("📊 Generated files:")
    print(f"  1. {left_file}")
    print("     • Core: users")
    print("     • Room Management: chat_rooms, messages, room_members, etc.")
    print("     • Skills: skills")
    print()
    print(f"  2. {right_file}")
    print("     • User Data: user_skills, user_preferences, training, life_events")
    print("     • System: error_logs, token_blacklist")
    print()
    print("🎨 Color coding:")
    print("   • Gray arrows = Internal relationships (within same diagram)")
    print("   • 🌈 COLORED arrows = Cross-diagram relationships")
    print("      → Each relationship has its own UNIQUE color")
    print("      → The SAME color appears in BOTH diagrams")
    print("      → Match colors to follow connections!")
    print()


if __name__ == '__main__':
    main()
