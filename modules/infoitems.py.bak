#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PhreakBot IRC Bot - Infoitems Module
# https://github.com/jskoetsier/phreakbot

import re
import logging
import traceback
from datetime import datetime

def config(bot):
    return {
        'events': ['message'],
        'commands': ['infoitem', 'infoitems'],
        'help': {
            'infoitem': 'Manage infoitems. Usage: !infoitem add <item> <value> | !infoitem del <item> | !infoitem list',
            'infoitems': 'List all infoitems. Usage: !infoitems'
        }
    }

class Module:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('PhreakBot')
        self.db = bot.db
        
        # Compile regex patterns for direct command handling
        # Support multiple formats for adding infoitems
        self.add_patterns = [
            re.compile(r'^!([a-zA-Z0-9_-]+)\s*=\s*(.+)$'),      # !item = value
            re.compile(r'^!([a-zA-Z0-9_-]+)\s+is\s+(.+)$'),     # !item is value
            re.compile(r'^!([a-zA-Z0-9_-]+)\+(.+)$'),           # !item+value
            re.compile(r'^!([a-zA-Z0-9_-]+):(.+)$')             # !item:value
        ]
        
        # Support multiple formats for retrieving infoitems
        self.get_patterns = [
            re.compile(r'^!([a-zA-Z0-9_-]+)\?$'),               # !item?
            re.compile(r'^!([a-zA-Z0-9_-]+)$')                  # !item
        ]
        
        pattern_descriptions = [p.pattern for p in self.add_patterns] + [p.pattern for p in self.get_patterns]
        self.logger.info(f"Infoitems module initialized with patterns: {pattern_descriptions}")

    async def handle_event(self, event):
        if event['event'] == 'message':
            message = event['message']
            channel = event['channel']
            user = event['user']
            
            self.logger.debug(f"Checking message '{message}' against infoitem patterns")
            
            # Check for add patterns
            for pattern in self.add_patterns:
                match = pattern.match(message)
                if match:
                    item = match.group(1)
                    value = match.group(2)
                    self.logger.info(f"Add match found: item={item}, value={value}")
                    await self.add_infoitem(channel, user, item, value)
                    return True
            
            # Check for get patterns
            for pattern in self.get_patterns:
                match = pattern.match(message)
                if match:
                    item = match.group(1)
                    # Skip if the item is a known command from another module
                    if item in self.bot.commands and item not in ['infoitem', 'infoitems']:
                        self.logger.debug(f"Skipping {item} as it's a known command")
                        continue
                    
                    self.logger.info(f"Get match found: item={item}")
                    await self.get_infoitem(channel, item)
                    return True
            
            # Handle standard commands
            parts = message.split()
            if len(parts) > 0 and parts[0] in ['!infoitem', '!infoitems']:
                if parts[0] == '!infoitems':
                    await self.list_infoitems(channel)
                    return True
                
                if len(parts) >= 2:
                    if parts[1] == 'list':
                        await self.list_infoitems(channel)
                        return True
                    elif parts[1] == 'add' and len(parts) >= 4:
                        item = parts[2]
                        value = ' '.join(parts[3:])
                        await self.add_infoitem(channel, user, item, value)
                        return True
                    elif parts[1] == 'del' and len(parts) >= 3:
                        item = parts[2]
                        await self.delete_infoitem(channel, user, item)
                        return True
        
        return False

    async def add_infoitem(self, channel, user, item, value):
        try:
            self.logger.info(f"Adding infoitem: {item}={value} in {channel} by {user}")
            
            # Check if item already exists
            cursor = self.db.cursor()
            cursor.execute("SELECT id FROM phreakbot_infoitems WHERE item = %s AND channel = %s", (item, channel))
            result = cursor.fetchone()
            
            if result:
                # Update existing item
                self.logger.info(f"Updating existing infoitem with ID {result[0]}")
                cursor.execute(
                    "UPDATE phreakbot_infoitems SET value = %s, username = %s, insert_time = NOW() WHERE id = %s",
                    (value, user, result[0])
                )
                await self.bot.send_message(channel, f"Updated infoitem: !{item}")
            else:
                # Insert new item
                self.logger.info(f"Creating new infoitem")
                cursor.execute(
                    "INSERT INTO phreakbot_infoitems (item, value, channel, username, insert_time) VALUES (%s, %s, %s, %s, NOW())",
                    (item, value, channel, user)
                )
                await self.bot.send_message(channel, f"Added infoitem: !{item}")
            
            self.db.commit()
            cursor.close()
            
            # Verify the item was added/updated
            cursor = self.db.cursor()
            cursor.execute("SELECT id FROM phreakbot_infoitems WHERE item = %s AND channel = %s", (item, channel))
            verify = cursor.fetchone()
            cursor.close()
            
            if verify:
                self.logger.info(f"Successfully added/updated infoitem with ID {verify[0]}")
            else:
                self.logger.error(f"Failed to add/update infoitem - not found after commit")
                
        except Exception as e:
            self.logger.error(f"Error adding infoitem: {e}")
            self.logger.error(traceback.format_exc())
            await self.bot.send_message(channel, f"Error adding infoitem: {str(e)}")

    async def get_infoitem(self, channel, item):
        try:
            self.logger.info(f"Getting infoitem: {item} from {channel}")
            
            cursor = self.db.cursor()
            cursor.execute("SELECT value, username, insert_time FROM phreakbot_infoitems WHERE item = %s AND channel = %s", (item, channel))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                value, username, insert_time = result
                formatted_time = insert_time.strftime('%Y-%m-%d') if insert_time else 'unknown date'
                await self.bot.send_message(channel, f"{item}: {value} (added by {username} on {formatted_time})")
                return True
            else:
                # Don't send a message if the item doesn't exist
                # This prevents confusion when users type !command that doesn't exist
                self.logger.debug(f"No infoitem found for !{item}")
                return False
        except Exception as e:
            self.logger.error(f"Error retrieving infoitem: {e}")
            self.logger.error(traceback.format_exc())
            await self.bot.send_message(channel, f"Error retrieving infoitem: {str(e)}")
        return True

    async def delete_infoitem(self, channel, user, item):
        try:
            self.logger.info(f"Deleting infoitem: {item} from {channel}")
            
            cursor = self.db.cursor()
            cursor.execute("DELETE FROM phreakbot_infoitems WHERE item = %s AND channel = %s RETURNING id", (item, channel))
            result = cursor.fetchone()
            self.db.commit()
            cursor.close()
            
            if result:
                await self.bot.send_message(channel, f"Deleted infoitem: !{item}")
            else:
                await self.bot.send_message(channel, f"No infoitem found for !{item}")
        except Exception as e:
            self.logger.error(f"Error deleting infoitem: {e}")
            self.logger.error(traceback.format_exc())
            await self.bot.send_message(channel, f"Error deleting infoitem: {str(e)}")

    async def list_infoitems(self, channel):
        try:
            self.logger.info(f"Listing infoitems for channel: {channel}")
            
            cursor = self.db.cursor()
            cursor.execute("SELECT item FROM phreakbot_infoitems WHERE channel = %s ORDER BY item", (channel,))
            items = cursor.fetchall()
            cursor.close()
            
            if items:
                item_list = ', '.join([f"!{item[0]}" for item in items])
                await self.bot.send_message(channel, f"Available infoitems: {item_list}")
            else:
                await self.bot.send_message(channel, "No infoitems available")
        except Exception as e:
            self.logger.error(f"Error listing infoitems: {e}")
            self.logger.error(traceback.format_exc())
            await self.bot.send_message(channel, f"Error listing infoitems: {str(e)}")