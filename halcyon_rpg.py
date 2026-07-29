"""
Halcyon Expanse - 2D Top-Down RPG
Main entry point. Run with: python halcyon_rpg.py
"""
import sys
import os
import time
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine2d.game_loop import Game2D


def print_banner():
    print("+" + "="*62 + "+")
    print("|" + " "*62 + "|")
    print("|" + "           H A L C Y O N   E X P A N S E".center(62) + "|")
    print("|" + "              2D Top-Down RPG v0.2.0".center(62) + "|")
    print("|" + " "*62 + "|")
    print("|" + "  Year 706 | 9 Star Systems | 7 Resonances | 6 Enemy Types".center(62) + "|")
    print("|" + " "*62 + "|")
    print("+" + "="*62 + "+")


def print_help():
    print("""
CONTROLS:
  w/a/s/d or arrows - Move
  space             - Attack (direction of last move)
  e                 - Interact (seam gates, items, NPCs)
  1-7               - Cast Lattice Ability
  i                 - Inventory
  c                 - Codex (lore entries)
  t                 - Status / Stats
  warp <system>     - Warp via Seam (when at gate)
  spawn <enemy>     - Spawn enemy (debug)
  exchange <amt> <from> <to> - Currency exchange
  q                 - Quit

ABILITIES:
  1: ember_strike  | 2: gale_dash  | 3: tide_heal
  4: hollow_drain  | 5: iron_shield | 6: root_bind
  7: chorus_blast

NEW COMMANDS:
  save [slot]       - Save game (slots 1-5)
  load [slot]       - Load game
  saves             - List save files
  quest/quests      - View active/available quests
  startquest <id>   - Start a quest
  equip/eq          - View equipped items
  level/xp          - View level and XP progress
  qlog              - View quest log
  boss/bosses       - View available/defeated bosses
  spawnboss <id>    - Spawn a boss (debug)
  craft/crafting    - View available recipes
  make <recipe>     - Craft an item
  time/clock        - Show time of day and weather
  events/world      - Show active world events
  talk <npc>        - Talk to an NPC
  sound             - Sound system info
  save [slot]       - Save game (slots 1-5)
  load [slot]       - Load game
  saves             - List save files
  quest/quests      - View active/available quests
  startquest <id>   - Start a quest
  equip/eq          - View equipped items
  level/xp          - View level and XP progress
  qlog              - View quest log
""")


def main():
    print_banner()

    print("Choose your Resonance:")
    resonances = ["Ember", "Gale", "Hollow", "Tide", "Root", "Iron", "Chorus"]
    for i, r in enumerate(resonances, 1):
        print(f"  {i}. {r}")

    choice = input("\nEnter number (1-7) or name: ").strip()
    try:
        idx = int(choice) - 1
        player_res = resonances[idx] if 0 <= idx < 7 else "Ember"
    except:
        player_res = choice if choice in resonances else "Ember"

    print(f"\nResonance: {player_res}")
    print("Initializing world...")

    game = Game2D(seed=78, player_resonance=player_res, use_visual=True)

    print("\n" + "="*60)
    print("WORLD LOADED")
    print("="*60)

    status = game.get_status()
    print(f"System: {status['system']} | Biome: {status['biome']}")
    print(f"Position: {status['position']}")
    print(f"HP: {status['hp']} | LC: {status['lc']:.0f}/{status['lc_max']:.0f}")
    print(f"Debt: {status['debt']:.2f} | Attunement: {status['attunement']}")
    print(f"Inventory: {status['inventory_count']} items")
    print(f"CS: {status['cs']:.2f} | LM: {status['lm']:.2f}")
    print(f"Enemies nearby: {status['enemies_nearby']}")
    print("="*60)

    print_help()

    last_dir = (0, -1)

    while True:
        try:
            cmd = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if not cmd:
            continue

        parts = cmd.split()
        action = parts[0]

        if action in ['w', 'up', 'north']:
            last_dir = (0, -1)
            result = game.move_player(0, -1)
            if result == "seam_gate":
                print("You stand before a SEAM GATE. Press E to interact.")
        elif action in ['s', 'down', 'south']:
            last_dir = (0, 1)
            result = game.move_player(0, 1)
            if result == "seam_gate":
                print("You stand before a SEAM GATE. Press E to interact.")
        elif action in ['a', 'left', 'west']:
            last_dir = (-1, 0)
            result = game.move_player(-1, 0)
            if result == "seam_gate":
                print("You stand before a SEAM GATE. Press E to interact.")
        elif action in ['d', 'right', 'east']:
            last_dir = (1, 0)
            result = game.move_player(1, 0)
            if result == "seam_gate":
                print("You stand before a SEAM GATE. Press E to interact.")

        elif action in ['space', 'attack', 'atk']:
            success, msg = game.attack(last_dir)
            print(msg)

        elif action in ['1', '2', '3', '4', '5', '6', '7']:
            abilities = ['ember_strike', 'gale_dash', 'tile_heal', 'hollow_drain', 
                        'iron_shield', 'root_bind', 'chorus_blast']
            ability_id = abilities[int(action) - 1]
            success, msg = game.cast_ability(ability_id)
            print(msg)

        elif action in ['e', 'interact']:
            result = game.interact()
            print(result)

        elif action == 'warp' and len(parts) > 1:
            target = parts[1].capitalize()
            target_map = {
                'Veyraprime': 'VeyraPrime', 'Ashduin': 'Ashduin', 'Tworivers': 'TwoRivers',
                'Hollowanchor': 'HollowAnchor', 'Galesreach': 'GalesReach',
                'Ironmeridian': 'IronMeridian', 'Chorusdeep': 'ChorusDeep',
                'Saltwastes': 'SaltWastes', 'Hushmarches': 'HushMarches'
            }
            target = target_map.get(target, target)
            msg = game.warp(target)
            print(msg)

        elif action in ['i', 'inventory', 'inv']:
            print(f"\nINVENTORY ({len(game.inventory.items)}/{game.inventory.capacity}):")
            for item in game.inventory.items:
                print(f"  [{item.rarity}] {item.name} ({item.item_type}) - {item.get_border_color()}")
            print(f"\nCS: {game.economy.get_balance('CS'):.2f} | LM: {game.economy.get_balance('LM'):.2f}")

        elif action in ['c', 'codex', 'lore']:
            unlocked = game.codex.get_unlocked()
            print(f"\nCODEX ({len(unlocked)}/{len(game.codex.entries)} entries unlocked):")
            for entry in unlocked:
                print(f"  Year {entry.year}: {entry.name}")
                print(f"    {entry.description}")

        elif action in ['t', 'status', 'stats']:
            s = game.get_status()
            print(f"\n{'='*50}")
            print(f"  RESONANCE: {s['resonance']} | ATTUNEMENT: {s['attunement']}/10")
            print(f"  HP: {s['hp']} | LC: {s['lc']:.0f}/{s['lc_max']:.0f}")
            print(f"  DEBT: {s['debt']:.2f} (3%/hr)")
            print(f"  SYSTEM: {s['system']} | BIOME: {s['biome']}")
            print(f"  POSITION: ({s['position'][0]:.1f}, {s['position'][1]:.1f})")
            print(f"  YEAR: {s['year']}")
            print(f"  ENEMIES NEARBY: {s['enemies_nearby']}")
            print(f"  INVENTORY: {s['inventory_count']} items")
            print(f"  CS: {s['cs']:.2f} | LM: {s['lm']:.2f}")
            if 'level' in s:
                print(f"  LEVEL: {s['level']}/10 | XP: {s['xp']:.0f}/{s['xp_to_next']:.0f} ({s['xp_progress']:.1f}%)")
            if 'active_quests' in s:
                print(f"  QUESTS: {s['active_quests']} active | {s['completed_quests']} completed")
            if 'play_time' in s:
                print(f"  PLAY TIME: {s['play_time']/60:.1f} minutes")
            print(f"{'='*50}")

        elif action == 'exchange' and len(parts) >= 4:
            try:
                amt = float(parts[1])
                from_c = parts[2].upper()
                to_c = parts[3].upper()
                result = game.economy.exchange(from_c, to_c, amt)
                if result:
                    print(f"Exchanged {amt} {from_c} -> {result:.2f} {to_c}")
                else:
                    print("Exchange failed")
            except:
                print("Usage: exchange <amount> <from> <to>")

        elif action == 'spawn' and len(parts) > 1:
            enemy_name = ' '.join(parts[1:]).title()
            enemy = game.bestiary.spawn(enemy_name)
            if enemy:
                enemy.x = game.player.x + 2
                enemy.y = game.player.y + 2
                print(f"Spawned {enemy.name} at ({enemy.x:.0f}, {enemy.y:.0f})")
            else:
                print(f"Unknown enemy: {enemy_name}")

        elif action in ['r', 'render', 'frame']:
            frame_path = os.path.join(os.path.dirname(__file__), 'frame.png')
            game.use_visual = False
            ascii_frame = game.render()
            game.use_visual = True
            if isinstance(ascii_frame, str):
                print(ascii_frame)
            else:
                img = game.render(output_path=frame_path)
                print(f"Frame rendered: {frame_path} ({img.size[0]}x{img.size[1]})")

        elif action in ['log', 'combat']:
            log = game.get_combat_log()
            if log:
                print("\nCOMBAT LOG:")
                for line in log:
                    print(f"  {line}")
            else:
                print("No combat log entries")

        elif action in ['h', 'help', '?']:
            print_help()

        elif action in ['q', 'quit', 'exit']:
            print("\nSaving state...")
            print("Goodbye, traveler.")
            break

        game.update()

        if game.player.hp <= 0:
            print("\n" + "="*60)
            print("  YOU HAVE DIED")
            print("  Your lattice fades into the void...")
            print("="*60)
            break

        nearby = [e for e in game.bestiary.enemies 
                  if math.sqrt((e.x-game.player.x)**2 + (e.y-game.player.y)**2) < 5]
        if nearby:
            print(f"\nWARNING: {len(nearby)} ENEMIES NEARBY")
            for e in nearby:
                dist = math.sqrt((e.x-game.player.x)**2 + (e.y-game.player.y)**2)
                print(f"  {e.name} (T{e.threat_tier}) [{e.hp}/{e.max_hp} HP] - {dist:.1f}m away, state: {e.state}")


if __name__ == "__main__":
    main()
