import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import Optional
import random

from uno_logic import Game, Card, COLORS


class UnoGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("UNO (Python)")
        self.root.geometry("1140x820")
        self.root.configure(bg="#1e1e1e")

        # Game state
        self.game: Optional[Game] = None
        self.bot_timer_id: Optional[str] = None
        self.turn_no: int = 1
        self._last_log: Optional[str] = None
        self._last_turn_owner: Optional[int] = None
        # Hand pagination (show up to 10 cards; show nav starting at 11th)
        self.HAND_PAGE_SIZE = 10
        self.hand_page = 0
        # Round-end guard
        self._round_end_processed = False

        # Match scoring
        self.scores = [0, 0, 0, 0]
        self.target_score = 500

        # Top frame
        self.info_frame = tk.Frame(root, bg="#1e1e1e")
        self.info_frame.pack(side=tk.TOP, fill=tk.X)
        self.turn_label = tk.Label(self.info_frame, text="", fg="#fff", bg="#1e1e1e", font=("Segoe UI", 14, "bold"))
        self.turn_label.pack(side=tk.LEFT, padx=10, pady=10)
        self.color_label = tk.Label(self.info_frame, text="", fg="#fff", bg="#1e1e1e", font=("Segoe UI", 14, "bold"))
        self.color_label.pack(side=tk.RIGHT, padx=10, pady=10)

        # Right: log + scoreboard + New Game
        self.right_panel = tk.Frame(root, bg="#1e1e1e")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        tk.Label(self.right_panel, text="Log", fg="#fff", bg="#1e1e1e", font=("Segoe UI", 12, "bold")).pack(anchor="n", pady=(8, 2))
        self.log_list = tk.Listbox(self.right_panel, bg="#252526", fg="#eee", width=38, height=22)
        self.log_list.pack(fill=tk.Y, padx=8, pady=4)
        sb = tk.LabelFrame(self.right_panel, text="Scoreboard (to 500)", fg="#ddd", bg="#1e1e1e", labelanchor="n")
        sb.pack(fill=tk.X, padx=8, pady=(6, 6))
        self.score_vars = [tk.StringVar() for _ in range(4)]
        self.score_labels = []
        for i in range(4):
            lbl = tk.Label(sb, textvariable=self.score_vars[i], fg="#fff", bg="#1e1e1e", font=("Segoe UI", 11))
            lbl.pack(anchor="w", padx=8, pady=2)
            self.score_labels.append(lbl)
        # New Game button below scoreboard
        self.new_button = tk.Button(self.right_panel, text="New Game", command=self.new_game, bg="#0e639c", fg="#fff", font=("Segoe UI", 11, "bold"), relief=tk.FLAT, padx=12, pady=8)
        self.new_button.pack(fill=tk.X, padx=12, pady=(2, 10))

        # Bots summary
        self.bots_frame = tk.Frame(root, bg="#1e1e1e")
        self.bots_frame.pack(side=tk.TOP, fill=tk.X, padx=12)
        self.bot_panels = []
        for _ in range(3):
            panel = tk.Frame(self.bots_frame, bg="#252526", padx=8, pady=6, relief=tk.RIDGE, bd=2)
            panel.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=6, pady=6)
            name = tk.Label(panel, text="", fg="#fff", bg="#252526", font=("Segoe UI", 11, "bold"))
            name.pack(anchor="w")
            info_row = tk.Frame(panel, bg="#252526")
            info_row.pack(fill=tk.X, pady=(2, 4))
            count = tk.Label(info_row, text="", fg="#ddd", bg="#252526", font=("Segoe UI", 10))
            count.pack(side=tk.LEFT)
            uno = tk.Label(info_row, text="", fg="#ff5f56", bg="#252526", font=("Segoe UI", 10, "bold"))
            uno.pack(side=tk.RIGHT)
            cards_container = tk.Frame(panel, bg="#252526")
            cards_container.pack(fill=tk.X)
            self.bot_panels.append({"frame": panel, "name": name, "count": count, "uno": uno, "cards": cards_container})

        # Center area with board centered
        self.center_frame = tk.Frame(root, bg="#252526")
        self.center_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Board row: deck (left) + discard (center)
        self.board_frame = tk.Frame(self.center_frame, bg="#252526")
        self.board_frame.pack(expand=True)
        self.deck_card = tk.Label(self.board_frame, text="Deck", fg="#eee", bg="#3a3a3a", width=12, height=6,
                                   font=("Segoe UI", 12, "bold"), relief=tk.RIDGE, bd=3)
        self.deck_card.pack(side=tk.LEFT, padx=30)
        self.discard_card = tk.Label(self.board_frame, text="-", fg="#111", bg="#ddd", width=22, height=8,
                                     font=("Segoe UI", 14, "bold"), relief=tk.RAISED, bd=4)
        self.discard_card.pack(side=tk.LEFT, padx=30)

        # Controls: draw/pass only, centered beneath board
        self.controls_frame = tk.Frame(self.center_frame, bg="#252526")
        self.controls_frame.pack(pady=8)
        self.draw_button = tk.Button(self.controls_frame, text="Draw card", command=self.on_draw, bg="#007acc", fg="#fff", font=("Segoe UI", 11, "bold"), relief=tk.FLAT, padx=12, pady=8)
        self.draw_button.grid(row=0, column=0, padx=6)
        self.pass_button = tk.Button(self.controls_frame, text="Pass", command=self.on_pass, bg="#3c3c3c", fg="#fff", font=("Segoe UI", 11), relief=tk.FLAT, padx=12, pady=8)
        self.pass_button.grid(row=0, column=1, padx=6)

        # Player hand
        self.hand_frame = tk.Frame(root, bg="#1e1e1e")
        self.hand_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=12)

        self.status_label = tk.Label(root, text="Welcome! Click 'New Game'.", fg="#fff", bg="#1e1e1e", font=("Segoe UI", 12))
        self.status_label.pack(side=tk.BOTTOM, pady=8)

        self.color_choice_frame = tk.Frame(self.center_frame, bg="#252526")
        self.color_buttons = []
        for c in COLORS:
            b = tk.Button(self.color_choice_frame, text=c, command=lambda col=c: self.on_choose_color(col), width=10,
                          font=("Segoe UI", 11, "bold"))
            self.color_buttons.append(b)

        # +4 decision panel (human)
        self.plus4_frame = tk.Frame(self.center_frame, bg="#252526")
        self.accept_btn = tk.Button(self.plus4_frame, text="Accept +4 (Draw 4)", command=lambda: self.on_plus4_decision('accept'), bg="#cc5c5c", fg="#fff")
        self.challenge_btn = tk.Button(self.plus4_frame, text="Challenge +4", command=lambda: self.on_plus4_decision('challenge'), bg="#f0ad4e", fg="#fff")
        self.accept_btn.pack(side=tk.LEFT, padx=6)
        self.challenge_btn.pack(side=tk.LEFT, padx=6)

        # UNO UI panels (hidden by default)
        self.uno_call_frame = tk.Frame(self.center_frame, bg="#252526")
        self.uno_call_btn = tk.Button(self.uno_call_frame, text="Call UNO!", command=self.on_call_uno, bg="#d19a66", fg="#fff", font=("Segoe UI", 12, "bold"))
        self.uno_call_btn.pack(side=tk.LEFT, padx=6)
        self.uno_challenge_frame = tk.Frame(self.center_frame, bg="#252526")
        self.uno_challenge_btn = tk.Button(self.uno_challenge_frame, text="Challenge UNO!", command=self.on_challenge_uno, bg="#e06c75", fg="#fff", font=("Segoe UI", 12, "bold"))
        self.uno_challenge_btn.pack(side=tk.LEFT, padx=6)

        # Start
        self.new_game()

    def log(self, text: str):
        entry = f"Turn {self.turn_no}: {text}" if text else ""
        if entry and entry != self._last_log:
            self.log_list.insert(tk.END, entry)
            self.log_list.yview_moveto(1)
            self._last_log = entry

    def update_scoreboard(self):
        if not self.game:
            return
        names = [p.name for p in self.game.players]
        for i in range(4):
            self.score_vars[i].set(f"{names[i]}: {self.scores[i]}")

    def new_game(self):
        self.game = Game(num_players=4)
        self.game.setup()
        self.turn_no = 0
        self._last_log = None
        self._last_turn_owner = self.game.current_index
        # Reset hand pager each round
        self.hand_page = 0
        self._round_end_processed = False
        self.log_list.delete(0, tk.END)
        self.status("Game started. Official rules, +4 challenge enabled. Draw 1 if you cannot play.")
        self.update_scoreboard()
        self.refresh()
        # Handle initial wild color choice if needed
        self.handle_pending_initials()
        self.schedule_bots(1000)

    def restart_match(self):
        self.scores = [0, 0, 0, 0]
        self.update_scoreboard()
        self.status("Match restarted.")
        self.new_game()

    def status(self, text: str):
        label_text = text
        try:
            if self.game and not self.game.game_over and self.game.current_index == 0 and self.game.pending_plus4 is None and self.game.pending_initial_wild_for is None:
                if "It's your turn!" not in label_text:
                    label_text = f"{label_text}  It's your turn!"
        except Exception:
            pass
        self.status_label.config(text=label_text)
        self.log(text)

    def handle_pending_initials(self):
        g = self.game
        if not g:
            return
        # If initial Wild requires a color choice
        if g.pending_initial_wild_for is not None:
            if g.pending_initial_wild_for == 0:
                # Human: show picker
                self.show_color_picker(initial=True)
                self.status("Starting card is Wild. Choose the starting color.")
            else:
                # Bot chooses color automatically
                color = g.choose_color_for_bot(g.pending_initial_wild_for)
                g.set_initial_wild_color(color)
                self.status(f"{g.players[g.pending_initial_wild_for].name} chose starting color {color}.")
                self.refresh()

    def card_bg_for(self, card: Card) -> str:
        if card.is_wild():
            return "#dddddd"
        mp = {"Red": "#ff5f56", "Yellow": "#ffd866", "Green": "#5af78e", "Blue": "#57c7ff"}
        return mp.get(card.color or "", "#ddd")

    def dim_card_bg_for(self, card: Card) -> str:
        """Return a dimmer background color for non-playable cards to 'unlight' them."""
        if card.is_wild():
            return "#eeeeee"
        mp_dim = {"Red": "#f8a09b", "Yellow": "#f5e49a", "Green": "#a8f1c2", "Blue": "#a6e3ff"}
        return mp_dim.get(card.color or "", "#eee")

    def refresh(self):
        if not self.game:
            return
        g = self.game
        top = g.top_card()
        # Colorize discard: if wild, show chosen color and tint background accordingly
        display_text = top.display()
        discard_bg = self.card_bg_for(top)
        if top.is_wild():
            chosen = g.current_color
            if chosen in COLORS:
                # Map chosen color directly
                color_map = {"Red": "#ff5f56", "Yellow": "#ffd866", "Green": "#5af78e", "Blue": "#57c7ff"}
                discard_bg = color_map.get(chosen, "#dddddd")
                display_text = f"{display_text} → {chosen}"
            else:
                discard_bg = "#dddddd"
        self.discard_card.config(text=display_text, bg=discard_bg, fg="#000" if not top.is_wild() else "#111")
        # Update deck visual with remaining count
        try:
            deck_count = len(g.deck.cards)
            self.deck_card.config(text=f"Deck\n{deck_count} left")
        except Exception:
            pass

        order_hint = " → ".join([p.name for p in g.players])
        self.turn_label.config(text=f"Turn: {g.current_player().name}  (Direction: {'↻' if g.direction==1 else '↺'})  Order: {order_hint}")
        col = g.current_color if g.current_color else (top.color or '-')
        self.color_label.config(text=f"Current color: {col}")

        # Toggle +4 decision UI
        if g.is_plus4_pending_for(0):
            if not self.plus4_frame.winfo_ismapped():
                self.plus4_frame.pack(pady=8)
                self.status("You were hit by +4. Accept or Challenge.")
        else:
            if self.plus4_frame.winfo_ismapped():
                self.plus4_frame.pack_forget()

        # Render bots
        self.render_bots()

        # Render player's hand with pagination (using packed containers)
        for w in list(self.hand_frame.children.values()):
            w.destroy()
        if g.players[0].is_human:
            hand = g.players[0].hand
            total = len(hand)
            page_size = self.HAND_PAGE_SIZE
            total_pages = max(1, (total + page_size - 1) // page_size)
            if self.hand_page > total_pages - 1:
                self.hand_page = max(0, total_pages - 1)
            start = self.hand_page * page_size
            end = min(start + page_size, total)

            show_pager = total > page_size
            if show_pager:
                nav = tk.Frame(self.hand_frame, bg="#1e1e1e")
                nav.pack(anchor="w", pady=(0, 6))
                prev_btn = tk.Button(nav, text="◀ Prev", command=self.on_hand_prev,
                                     state=(tk.NORMAL if self.hand_page > 0 else tk.DISABLED),
                                     bg="#3c3c3c", fg="#fff", relief=tk.FLAT)
                prev_btn.pack(side=tk.LEFT, padx=4)
                info = tk.Label(nav, text=f"Cards {start+1}-{end} of {total}", fg="#ddd", bg="#1e1e1e")
                info.pack(side=tk.LEFT, padx=8)
                next_btn = tk.Button(nav, text="Next ▶", command=self.on_hand_next,
                                     state=(tk.NORMAL if self.hand_page < total_pages - 1 else tk.DISABLED),
                                     bg="#3c3c3c", fg="#fff", relief=tk.FLAT)
                next_btn.pack(side=tk.LEFT, padx=4)

            cards_container = tk.Frame(self.hand_frame, bg="#1e1e1e")
            cards_container.pack(anchor="w")

            # Use object identity for allowed moves to avoid issues with duplicate-equal cards
            allowed_ids = set(id(c) for c in (g.allowed_moves(0) if g.current_index == 0 else []))
            for card in hand[start:end]:
                playable = id(card) in allowed_ids
                bg = self.card_bg_for(card) if playable else self.dim_card_bg_for(card)
                fg = ("#000" if not card.is_wild() else "#111") if playable else "#777"
                btn = tk.Button(cards_container, text=card.display(), width=12, height=2,
                                bg=bg, fg=fg, activebackground=bg, cursor=("hand2" if playable else "arrow"),
                                relief=(tk.RAISED if playable else tk.FLAT), bd=(3 if playable else 1),
                                highlightthickness=(2 if playable else 0), highlightbackground=("#ffffff" if playable else "#1e1e1e"),
                                state=(tk.NORMAL if playable else tk.DISABLED),
                                command=(lambda c=card: self.on_play(c)) if playable else None)
                btn.pack(side=tk.LEFT, padx=4, pady=4)

        # Controls enablement
        is_human_turn = g.current_index == 0
        blocked = g.is_plus4_pending() or (g.pending_initial_wild_for is not None and g.pending_initial_wild_for == 0)
        can_draw, _ = (False, None)
        can_pass, _ = (False, None)
        if is_human_turn and not blocked:
            can_draw, _ = g.can_draw(0)
            can_pass, _ = g.can_pass(0)
        self.draw_button.config(state=(tk.NORMAL if can_draw else tk.DISABLED))
        self.pass_button.config(state=(tk.NORMAL if can_pass else tk.DISABLED))

        # End-of-round
        if g.game_over and g.winner_index is not None:
            self.handle_round_end()

        # Ensure bot progression if it's their turn and nothing is pending (e.g., after +4 accept)
        if (not g.game_over and g.current_index != 0 and not g.is_plus4_pending()
                and not (g.pending_initial_wild_for is not None and g.pending_initial_wild_for != 0)):
            try:
                # If no bot action is queued, queue one
                if not self.bot_timer_id:
                    self.schedule_bots(600)
            except Exception:
                # Fallback to immediate scheduling
                self.schedule_bots(600)

    def handle_round_end(self):
        # Prevent running multiple times
        if self._round_end_processed:
            return
        self._round_end_processed = True
        g = self.game
        if not g or g.winner_index is None:
            return
        winner = g.players[g.winner_index].name
        points = g.winner_points()
        # Update scoreboard
        self.scores[g.winner_index] += points
        self.update_scoreboard()
        # Show modal
        try:
            messagebox.showinfo("Round Over", f"{winner} wins the round and earns {points} points!")
        except Exception:
            pass
        # Check match end
        if self.scores[g.winner_index] >= self.target_score:
            try:
                messagebox.showinfo("Match Over", f"{winner} wins the match with {self.scores[g.winner_index]} points!")
            except Exception:
                pass
            # Auto restart match
            self.restart_match()
            return
        # Start next round shortly
        self.root.after(800, self.new_game)

    def render_bots(self):
        if not self.game:
            return
        g = self.game
        for i in range(1, 4):
            panel = self.bot_panels[i-1]
            player = g.players[i]
            panel["name"].config(text=f"{player.name}")
            count = len(player.hand)
            panel["count"].config(text=f"Cards: {count}")
            panel["uno"].config(text=("UNO!" if count == 1 else ""))
            for w in list(panel["cards"].children.values()):
                w.destroy()
            to_show = min(count, 12)
            for j in range(to_show):
                lbl = tk.Label(panel["cards"], text=" ", bg="#ddd", width=2, height=1, relief=tk.RIDGE)
                lbl.pack(side=tk.LEFT, padx=1, pady=1)
            if count > to_show:
                more = tk.Label(panel["cards"], text=f"+{count - to_show}", fg="#ddd", bg="#252526", font=("Segoe UI", 10))
                more.pack(side=tk.LEFT, padx=4)

    def on_play(self, card: Card):
        if not self.game:
            return
        g = self.game
        if g.current_index != 0:
            return
        allowed = g.allowed_moves(0)
        if card not in allowed:
            self.status("Move not allowed now.")
            return
        chosen_color = None
        if card.is_wild():
            self.show_color_picker(initial=False)
            self.pending_card = card
            return
        target_idx = g.next_player_index(1)
        ok, err = g.play_card(0, card, chosen_color)
        if not ok:
            self.status(err or "Invalid move")
            return
        self.turn_no += 1
        msg = f"You played {card.display()}"
        if card.value == "+4":
            msg += ". Waiting for target to accept or challenge."
        elif card.value == "+2":
            victim = g.players[target_idx].name
            msg += f". {victim} drew 2 and was skipped."
        elif card.value == "Skip":
            victim = g.players[target_idx].name
            msg += f". {victim} was skipped."
        elif card.value == "Reverse":
            msg += f". Direction reversed."
        self.status(msg)
        self.refresh()
        if not g.game_over:
            self.schedule_bots(1000)

    def show_color_picker(self, initial: bool = False):
        for w in list(self.color_choice_frame.children.values()):
            w.destroy()
        self.color_buttons.clear()
        for c in COLORS:
            b = tk.Button(self.color_choice_frame, text=c, command=lambda col=c, init=initial: self.on_choose_color(col, init), width=10,
                          font=("Segoe UI", 11, "bold"))
            b.pack(side=tk.LEFT, padx=6)
            self.color_buttons.append(b)
        self.color_choice_frame.pack(pady=8)
        self.status("Choose a color for the Wild")

    def on_choose_color(self, color: str, initial: bool = False):
        if not self.game:
            return
        self.color_choice_frame.pack_forget()
        g = self.game
        if initial:
            ok, err = g.set_initial_wild_color(color)
            if not ok:
                self.status(err or "Error setting initial color")
                return
            self.status(f"Starting color set to {color}.")
            self.refresh()
            self.schedule_bots(500)
            return
        card = getattr(self, 'pending_card', None)
        if not card:
            return
        target_idx = g.next_player_index(1)
        ok, err = g.play_card(0, card, chosen_color=color)
        self.pending_card = None
        if not ok:
            self.status(err or "Error playing Wild")
            return
        self.turn_no += 1
        msg = f"You played {card.display()} choosing {color}"
        if card.value == "+4":
            msg += ". Waiting for target to accept or challenge."
        self.status(msg)
        self.refresh()
        if not self.game.game_over:
            self.schedule_bots(1000)

    def on_draw(self):
        if not self.game:
            return
        g = self.game
        if g.current_index != 0:
            return
        ok, err, card = g.draw_one_action(0)
        if not ok:
            self.status(err or "Cannot draw now")
            return
        can_play_drawn = g.is_playable(card)
        if not can_play_drawn:
            self.turn_no += 1
            self.status(f"Drew: {card.display()}. Cannot play. Passing turn...")
            g.advance_turn(1)
            self.refresh()
            if not g.game_over:
                self.schedule_bots(1000)
            return
        self.status(f"Drew: {card.display()}. You can play this card.")
        self.refresh()

    def on_pass(self):
        if not self.game:
            return
        g = self.game
        if g.current_index != 0:
            return
        ok, err = g.can_pass(0)
        if not ok:
            self.status(err or "Cannot end turn now")
            return
        self.turn_no += 1
        g.advance_turn(1)
        self.status("Turn ended.")
        self.refresh()
        if not g.game_over:
            self.schedule_bots(1000)

    def on_plus4_decision(self, decision: str):
        g = self.game
        if not g or not g.is_plus4_pending_for(0):
            return
        if decision == 'accept':
            ok, err = g.accept_plus4(0)
            if ok:
                self.turn_no += 1
                self.status("You accepted +4 and drew 4 cards; your turn is skipped.")
        else:
            ok, err, was_legal = g.challenge_plus4(0)
            if ok:
                self.turn_no += 1
                if was_legal:
                    # Challenge failed
                    self.status("Challenge failed. You drew 6 cards and were skipped.")
                else:
                    # Challenge succeeded
                    self.status("Challenge succeeded! The +4 was illegal. Opponent drew 4; it's your turn.")
        self.refresh()
        if not g.game_over:
            self.schedule_bots(1000)

    # ---- Bot turn ----
    def schedule_bots(self, delay_ms: int = 1000):
        if not self.game or self.game.game_over:
            return
        g = self.game
        # Handle +4 and initial wild and normal bot turns as before
        if g.is_plus4_pending() and g.pending_plus4.get('target') != 0:
            if self.bot_timer_id:
                try:
                    self.root.after_cancel(self.bot_timer_id)
                except Exception:
                    pass
            self.bot_timer_id = self.root.after(delay_ms, self.process_plus4_for_bot)
            return
        if g.pending_initial_wild_for is not None and g.pending_initial_wild_for != 0:
            if self.bot_timer_id:
                try:
                    self.root.after_cancel(self.bot_timer_id)
                except Exception:
                    pass
            self.bot_timer_id = self.root.after(delay_ms, self.process_initial_wild_for_bot)
            return
        if g.current_index == 0:
            if self.bot_timer_id:
                try:
                    self.root.after_cancel(self.bot_timer_id)
                except Exception:
                    pass
                self.bot_timer_id = None
            return
        if self.bot_timer_id:
            try:
                self.root.after_cancel(self.bot_timer_id)
            except Exception:
                pass
            self.bot_timer_id = None
        self.bot_timer_id = self.root.after(delay_ms, self.process_bot_turn)

    def process_initial_wild_for_bot(self):
        g = self.game
        if not g or g.pending_initial_wild_for is None or g.pending_initial_wild_for == 0:
            return
        idx = g.pending_initial_wild_for
        color = g.choose_color_for_bot(idx)
        g.set_initial_wild_color(color)
        self.status(f"{g.players[idx].name} chose starting color {color}.")
        self.refresh()
        self.schedule_bots(600)

    def process_plus4_for_bot(self):
        g = self.game
        if not g or not g.is_plus4_pending() or g.pending_plus4.get('target') == 0:
            return
        idx = g.pending_plus4['target']
        played_by = g.pending_plus4['played_by']
        # Simple decision: 50% chance to challenge
        if random.random() < 0.5:
            ok, _, was_legal = g.challenge_plus4(idx)
            if ok:
                self.turn_no += 1
                if was_legal:
                    self.status(f"{g.players[idx].name} challenged +4 and failed, drew 6 and was skipped.")
                else:
                    self.status(f"{g.players[idx].name} challenged +4 successfully. {g.players[played_by].name} drew 4.")
        else:
            ok, _ = g.accept_plus4(idx)
            if ok:
                self.turn_no += 1
                self.status(f"{g.players[idx].name} accepted +4 and drew 4.")
        self.refresh()
        self.schedule_bots(600)

    def process_bot_turn(self):
        self.bot_timer_id = None
        if not self.game:
            return
        g = self.game
        if g.game_over or g.current_index == 0:
            return
        idx = g.current_index
        player = g.players[idx]
        action, play, color = g.choose_best_move(idx)
        if action == "play" and play is not None:
            target_idx = g.next_player_index(1)
            ok, err = g.play_card(idx, play, chosen_color=color)
            if not ok:
                action = "draw"
        if action == "draw" or play is None:
            ok, _, drawn = g.draw_one_action(idx)
            if ok and drawn and g.is_playable(drawn):
                color2 = g.choose_color_for_bot(idx) if drawn.is_wild() else None
                g.play_card(idx, drawn, chosen_color=color2)
                self.turn_no += 1
                self.status(f"{player.name} drew and played {drawn.display()}{' choosing ' + color2 if color2 else ''}.")
            else:
                g.advance_turn(1)
                self.turn_no += 1
                self.status(f"{player.name} drew and ended the turn.")
        else:
            msg = f"{player.name} played {play.display()}"
            if color:
                msg += f" choosing {color}"
            self.turn_no += 1
            if play.value == "+4":
                msg += ". Waiting for target to accept or challenge."
            elif play.value == "+2":
                victim = g.players[target_idx].name
                msg += f". {victim} drew 2 and was skipped."
            elif play.value == "Skip":
                victim = g.players[target_idx].name
                msg += f". {victim} was skipped."
            elif play.value == "Reverse":
                msg += f". Direction reversed."
            self.status(msg)
        self.refresh()
        if not g.game_over and g.current_index != 0:
            self.schedule_bots(1000)

    def on_call_uno(self):
        if not self.game or self.game.current_index != 0:
            return
        ok, err = self.game.call_uno(0)
        if ok:
            self.status("UNO! You have one card left.")
        else:
            self.status(err or "Error calling UNO")

    def on_challenge_uno(self):
        if not self.game or self.game.current_index != 0:
            return
        ok, err = self.game.challenge_uno(0)
        if ok:
            self.status("Challenge successful! Opponent had more than 2 cards.")
        else:
            self.status(err or "Error challenging UNO")

    def on_hand_prev(self):
        if not self.game:
            return
        if self.hand_page > 0:
            self.hand_page -= 1
            self.refresh()

    def on_hand_next(self):
        if not self.game:
            return
        total = len(self.game.players[0].hand) if self.game and self.game.players else 0
        total_pages = max(1, (total + self.HAND_PAGE_SIZE - 1) // self.HAND_PAGE_SIZE)
        if self.hand_page < total_pages - 1:
            self.hand_page += 1
            self.refresh()

def main():
    root = tk.Tk()
    UnoGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
