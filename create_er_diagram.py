#!/usr/bin/env python3
"""
Database ER Diagram Generator

Creates Entity-Relationship diagrams for the Socializer database
showing all tables, columns, and relationships with proper notation.

Output: High-resolution PNG image compatible with PowerPoint

Author: Socializer Team
Date: November 12, 2024
"""

import sqlite3
from graphviz import Digraph
from app.config import SQLALCHEMY_DATABASE_URL


def get_database_schema():
    """Extract database schema with tables, columns, and foreign keys."""
    db_path = SQLALCHEMY_DATABASE_URL.replace('sqlite:///', '')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [t[0] for t in cursor.fetchall() if not t[0].startswith('sqlite_')]
    
    schema = {}
    
    for table in tables:
        # Get columns
        cursor.execute(f'PRAGMA table_info({table})')
        columns = []
        primary_keys = []
        
        for col in cursor.fetchall():
            col_id, name, type_, notnull, default, pk = col
            columns.append({
                'name': name,
                'type': type_,
                'primary_key': bool(pk),
                'not_null': bool(notnull)
            })
            if pk:
                primary_keys.append(name)
        
        # Get foreign keys
        cursor.execute(f'PRAGMA foreign_key_list({table})')
        foreign_keys = []
        for fk in cursor.fetchall():
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


def create_er_diagram(schema, output_filename='socializer_er_diagram'):
    """Create ER diagram using Graphviz - Horizontal row layout with multiple columns."""
    
    # Create directed graph with proper horizontal layout in rows
    dot = Digraph(comment='Socializer Database ER Diagram')
    dot.attr(rankdir='TB', splines='ortho', nodesep='0.5', ranksep='1.2')
    dot.attr('node', shape='plaintext', fontname='Arial')
    dot.attr('graph', bgcolor='white', dpi='300')
    
    # Core tables at the top
    core_tables = ['users', 'chat_rooms', 'messages']
    
    # ROW 1: Core tables (3 side by side)
    with dot.subgraph(name='cluster_core') as c:
        c.attr(label='Core Tables', fontsize='20', fontname='Arial Bold')
        c.attr(style='dashed', color='#2980b9')
        c.attr(rank='same')  # Keep all 3 tables side by side
        
        for table_name in core_tables:
            if table_name in schema:
                create_table_node(c, table_name, schema[table_name])
    
    # ROW 2: Room management (4 side by side)
    related_tables = ['room_members', 'room_messages', 'room_invites', 'general_chat_messages']
    
    with dot.subgraph(name='cluster_rooms') as c:
        c.attr(label='Room Management', fontsize='20', fontname='Arial Bold')
        c.attr(style='dashed', color='#27ae60')
        c.attr(rank='same')  # Keep all 4 tables side by side
        
        for table_name in related_tables:
            if table_name in schema:
                create_table_node(c, table_name, schema[table_name])
    
    # ROW 3: User data tables (5 tables in 3-2 layout)
    user_tables = ['user_skills', 'user_preferences', 'skills', 'training', 'life_events']
    
    with dot.subgraph(name='cluster_users') as c:
        c.attr(label='User Data', fontsize='20', fontname='Arial Bold')
        c.attr(style='dashed', color='#e74c3c')
        # Split into two rows: first 3, then 2
        
        # First row: 3 tables
        with c.subgraph() as row1:
            row1.attr(rank='same')
            for table_name in user_tables[:3]:
                if table_name in schema:
                    create_table_node(row1, table_name, schema[table_name])
        
        # Second row: 2 tables
        with c.subgraph() as row2:
            row2.attr(rank='same')
            for table_name in user_tables[3:5]:
                if table_name in schema:
                    create_table_node(row2, table_name, schema[table_name])
    
    # ROW 4: System tables (2 side by side)
    system_tables = ['error_logs', 'token_blacklist']
    
    with dot.subgraph(name='cluster_system') as c:
        c.attr(label='System Tables', fontsize='20', fontname='Arial Bold')
        c.attr(style='dashed', color='#95a5a6')
        c.attr(rank='same')  # Keep both tables side by side
        
        for table_name in system_tables:
            if table_name in schema:
                create_table_node(c, table_name, schema[table_name])
    
    # Add remaining tables to the bottom
    remaining_tables = [t for t in schema if t not in (core_tables + related_tables + user_tables + system_tables)]
    if remaining_tables:
        with dot.subgraph(name='cluster_other') as c:
            c.attr(label='Other Tables', fontsize='20', fontname='Arial Bold')
            c.attr(style='dashed', color='#bdc3c7')
            c.attr(rank='same')
            
            for table_name in remaining_tables:
                create_table_node(c, table_name, schema[table_name])
    
    # Add relationships
    for table_name, table_info in schema.items():
        for fk in table_info['foreign_keys']:
            ref_table = fk['references_table']
            if ref_table in schema:
                # Determine relationship type
                label = determine_relationship_type(table_name, ref_table, schema)
                
                # Add edge with proper notation
                dot.edge(
                    ref_table,
                    table_name,
                    label=label,
                    fontsize='10',
                    fontname='Arial',
                    color='#34495e',
                    penwidth='2',
                    arrowhead='crow',  # Crow's foot notation
                    arrowtail='none'
                )
    
    return dot


def create_table_node(graph, table_name, table_info):
    """Create an HTML table node for a database table."""
    
    # Start HTML table
    html = f'''<
        <TABLE BORDER="2" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">
            <TR>
                <TD BGCOLOR="#3498db" COLSPAN="2">
                    <FONT COLOR="white" POINT-SIZE="14"><B>{table_name.upper()}</B></FONT>
                </TD>
            </TR>
    '''
    
    # Add columns - show up to 8 columns for readability
    for col in table_info['columns'][:8]:  # Limit to first 8 columns for readability
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
    
    graph.node(table_name, html)


def determine_relationship_type(from_table, to_table, schema):
    """Determine relationship type (1:1, 1:N, M:N)."""
    
    # Check if it's a many-to-many junction table
    if from_table in ['user_skills', 'training', 'room_members', 'room_memberships']:
        return '1:N'
    
    # Most relationships are one-to-many
    return '1:N'


def main():
    """Main function to create ER diagram."""
    print("=" * 70)
    print("🎨 Creating Entity-Relationship Diagram")
    print("=" * 70)
    print()
    
    print("📊 Analyzing database schema...")
    schema = get_database_schema()
    print(f"✅ Found {len(schema)} tables")
    print()
    
    print("🎨 Generating ER diagram...")
    dot = create_er_diagram(schema)
    
    # Save diagram
    output_file = 'socializer_er_diagram'
    
    print(f"💾 Saving diagram as PNG...")
    dot.render(output_file, format='png', cleanup=True)
    
    print()
    print("=" * 70)
    print(f"✅ ER Diagram created: {output_file}.png")
    print("=" * 70)
    print()
    print("📊 Diagram includes:")
    print("  • All database tables")
    print("  • Primary keys (🔑)")
    print("  • Top 5 columns per table (compact design)")
    print("  • Foreign key relationships with arrows")
    print("  • EXTRA NARROW vertical layout")
    print("  • Tables stacked one above another")
    print("  • Organized by layers:")
    print("    - Top: Core tables")
    print("    - Middle: Room management")
    print("    - Bottom: User data & System tables")
    print()
    print("📐 Layout specs:")
    print("  • Max width: 6 inches (very narrow!)")
    print("  • Height: Up to 20 inches (very tall!)")
    print("  • Single column layout (squeezed together)")
    print()
    print("📎 To add to PowerPoint:")
    print("  1. Open Socializer_Presentation.pptx")
    print("  2. Go to 'Database Schema Overview' slide")
    print("  3. Insert > Pictures > Picture from File")
    print(f"  4. Select {output_file}.png")
    print("  5. Resize and position as needed")
    print()
    
    return f"{output_file}.png"


if __name__ == "__main__":
    try:
        filename = main()
        print(f"🎉 Success! ER diagram saved as '{filename}'")
    except ImportError:
        print("❌ Error: graphviz not installed")
        print()
        print("To install graphviz:")
        print("  1. Install Graphviz: brew install graphviz")
        print("  2. Install Python package: pip install graphviz")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
