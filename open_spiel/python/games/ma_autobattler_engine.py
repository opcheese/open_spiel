import logging

logger = logging.getLogger("somelogger")

class Card():
    def __init__(self, stat, ability,suit,side_num):
        #self.priority = priority
        self.stat = stat
        self.is_dead = False
        self.ability = ability
        self.initial_stat = stat
        self.suit = suit
        self.swang_called = False
        self.side_num = side_num

    def take_damage(self,damage):
        self.stat -= damage
        if self.stat <= 0:
            self.is_dead = True
    
    def buf_amount(self,amount):
        self.stat += amount
        if self.stat <= 0:
            self.is_dead = True
    
    def debut(self,state,side_num):
         self.ability.debut(state,side_num,self)

    def performance(self,state):
         self.ability.performance(state,self)


    def swangsong(self,state,side_num):
         if not self.swang_called:
            self.swang_called = True
            self.ability.swangsong(state,side_num,self)
    
    def __str__(self):
        res = "intial {}| current {}|suit {}| ability {}".format(self.initial_stat,self.stat,self.suit, str(self.ability))
        return res
    
    def __repr__(self):
        return self.__str__()



class BasicAbility():
    """Just stats"""
    def __init__(self):
        pass
    
    def debut(self,state,side_num,card):
        side =  state.left_side if side_num ==0 else state.right_side
        while len(side) > 0:
            for card in side:
                state.kill_card(card)
        state.clean_up()
        
    def swangsong(self,state,side_num,card):
        pass

    def performance(self,state,card):
        pass

    def __str__(self):
        res =  type(self).__name__
        return res

class EaterAbility(BasicAbility):
    """Increase stats if same suit"""
    def __init__(self):
        pass
    
    def debut(self,state,side_num,card):
        side =  state.left_side if side_num ==0 else state.right_side
        while len(side) > 0:
            for old_card in side:
                if card.suit == old_card.suit:
                    state.buf_amount(card,old_card.stat)
                state.kill_card(old_card)
        state.clean_up()
        


    def __str__(self):
        res =  type(self).__name__
        return res

class GrowerAbility(BasicAbility):
    """Inscrease stat by 2 if same stat"""
    def __init__(self):
        pass
    
    def debut(self,state,side_num,card):
        side =  state.left_side if side_num ==0 else state.right_side
        while len(side) > 0:
            for old_card in side:
                if card.stat == old_card.stat:
                    state.buf_amount(card,old_card.stat+2)
                state.kill_card(old_card)
        state.clean_up()
        


    def __str__(self):
        res =  type(self).__name__
        return res

class FighterAbility(BasicAbility):
    """double stat if enemy of the same suit"""
    def __init__(self):
        pass

    def performance(self,state,card):
        side =  state.left_side if card.side_num ==1 else state.right_side
        enemy = side[0]
        if not enemy.suit==card.suit:
            state.buf_amount(card,card.stat)

class DavidAbility(BasicAbility):
    """Get stat equal to enemy"""
    def __init__(self):
        pass

    def performance(self,state,card):
        side =  state.left_side if card.side_num ==1 else state.right_side
        enemy = side[0]
        state.set_stat(card,enemy.stat)
        
class MartyrdomAbility(BasicAbility):
    """Do 2 damage to enemy on death"""
    def __init__(self):
        super().__init__()

    def swangsong(self,state,side_num,card):
        side =  state.left_side if side_num ==1 else state.right_side
        for card in side:
          card.take_damage(2)
          #if (card.stat>3):
          #state.kill_card(card)
        state.clean_up()

class TokenAbility(BasicAbility):
    """create a 1 stat token of the same suit on death"""
    def __init__(self):
        pass
        
    def swangsong(self,state,side_num,card):
        side =  state.left_side if side_num ==0 else state.right_side
        token = state.create_card(1,0,card.suit)
        state.add_card(token,side_num)

class ToxicAbility(BasicAbility):
    """on death buff enemy"""
    def __init__(self):
        pass
        
    def swangsong(self,state,side_num,card):
        side = state.left_side if side_num ==1 else state.right_side
        if len(side)>0:
            state.buf_amount(side[0],2)
            #side[0].stat+=2

class InfestAbility(BasicAbility):
   """On play do 2 damage if no enemy create a tocix token""" 
   def __init__(self):
        pass
    
   def debut(self,state,side_num,card):
        state.clean_up()
        side =  state.left_side if side_num ==1 else state.right_side
        if len(side)>0:
            state.take_damage(side[0],2)
          #side[0].take_damage(2)
        else:
            token = state.create_card(1,-1,card.suit)
            state.add_card(token,(side_num+1)%2)
        state.clean_up()

class GameLogEntry():
    def __init__(self):
        self.evet_name = "None"
    


class TakingDamage(GameLogEntry):
    def __init__(self,pre_state_str,damage):
        self.evet_name = "TakingDamage"
        self.pre_state_str = pre_state_str
        self.damage = damage

    def __str__(self):
        res = ""
        res = "{}!{}!{}".format(self.evet_name,self.pre_state_str,self.damage)
        return res

class TookDamage(GameLogEntry):
    def __init__(self,pre_state_str, damage,post_state_str):
        self.evet_name = "TookDamage"
        self.pre_state_str = pre_state_str
        self.post_state_str = post_state_str

        self.damage = damage

    def __str__(self):
        res = ""
        res = "{}!{}!{}!{}".format(self.evet_name,self.pre_state_str,self.damage,self.post_state_str)
        return res


class BuffingAmount(GameLogEntry):
    def __init__(self,pre_state_str,amount):
        self.evet_name = "BuffingAmount"
        self.pre_state_str = pre_state_str
        self.amount = amount

    def __str__(self):
        res = ""
        res = "{}!{}!{}".format(self.evet_name,self.pre_state_str,self.amount)
        return res

class BuffedAmount(GameLogEntry):
    def __init__(self,pre_state_str, amount,post_state_str):
        self.evet_name = "BuffedAmount"
        self.pre_state_str = pre_state_str
        self.post_state_str = post_state_str

        self.amount = amount

    def __str__(self):
        res = ""
        res = "{}!{}!{}!{}".format(self.evet_name,self.pre_state_str,self.amount,self.post_state_str)
        return res

class SettingStat(GameLogEntry):
    def __init__(self,pre_state_str,stat):
        self.evet_name = "SettingStat"
        self.pre_state_str = pre_state_str
        self.stat = stat

    def __str__(self):
        res = ""
        res = "{}!{}!{}".format(self.evet_name,self.pre_state_str,self.stat)
        return res

class SetStat(GameLogEntry):
    def __init__(self,pre_state_str, stat,post_state_str):
        self.evet_name = "SetStat"
        self.pre_state_str = pre_state_str
        self.post_state_str = post_state_str

        self.stat = stat

    def __str__(self):
        res = ""
        res = "{}!{}!{}!{}".format(self.evet_name,self.pre_state_str,self.stat,self.post_state_str)
        return res


class DebutingCard(GameLogEntry):
    def __init__(self,pre_state_str,card,side_num):
        self.evet_name = "DebutingCard"
        self.pre_state_str = pre_state_str
        self.card = str(card)
        self.side_num = side_num

    def __str__(self):
        res = ""
        res = "{}!{}!{}".format(self.evet_name,self.pre_state_str,self.card, self.side_num)
        return res

class DebutedCard(GameLogEntry):
    def __init__(self,pre_state_str, card,side_num,post_state_str):
        self.evet_name = "DebutedCard"
        self.pre_state_str = pre_state_str
        self.post_state_str = post_state_str
        self.side_num = side_num

        self.card = str(card)

    def __str__(self):
        res = ""
        res = "{}!{}!{}!{}!{}".format(self.evet_name,self.pre_state_str,self.card,self.side_num,self.post_state_str)
        return res


class SwaningCard(GameLogEntry):
    def __init__(self,pre_state_str,card,side_num):
        self.evet_name = "SwaningCard"
        self.pre_state_str = pre_state_str
        self.card = str(card)
        self.side_num = side_num

    def __str__(self):
        res = ""
        res = "{}!{}!{}".format(self.evet_name,self.pre_state_str,self.card, self.side_num)
        return res


class SwanedCard(GameLogEntry):
    def __init__(self,pre_state_str, card,side_num,post_state_str):
        self.evet_name = "SwanedCard"
        self.pre_state_str = pre_state_str
        self.post_state_str = post_state_str
        self.side_num = side_num

        self.card = str(card)

    def __str__(self):
        res = ""
        res = "{}!{}!{}!{}!{}".format(self.evet_name,self.pre_state_str,self.card,self.side_num,self.post_state_str)
        return res


class PreBattleCard(GameLogEntry):
    def __init__(self,pre_state_str,card,side_num):
        self.evet_name = "PreBattleCard"
        self.pre_state_str = pre_state_str
        self.card = str(card)
        self.side_num = side_num

    def __str__(self):
        res = ""
        res = "{}!{}!{}!{}".format(self.evet_name,self.pre_state_str,self.card, self.side_num)
        return res

class PreBattleDone(GameLogEntry):
    def __init__(self,pre_state_str, card,side_num,post_state_str):
        self.evet_name = "PreBattleDone"
        self.pre_state_str = pre_state_str
        self.post_state_str = post_state_str
        self.side_num = side_num

        self.card = str(card)

    def __str__(self):
        res = ""
        res = "{}!{}!{}!{}!{}".format(self.evet_name,self.pre_state_str,self.card,self.side_num,self.post_state_str)
        return res

class Battle(GameLogEntry):
    def __init__(self,pre_state_str):
        self.evet_name = "Battle"
        self.pre_state_str = pre_state_str


    def __str__(self):
        res = ""
        res = "{}".format(self.evet_name,self.pre_state_str)
        return res

class PostBattle(GameLogEntry):
    def __init__(self,pre_state_str, post_state_str):
        self.evet_name = "PostBattle"
        self.pre_state_str = pre_state_str
        self.post_state_str = post_state_str



    def __str__(self):
        res = ""
        res = "{}!{}".format(self.evet_name,self.pre_state_str,self.post_state_str)
        return res

class GameStart(GameLogEntry):
    def __init__(self,left_deck, right_deck):
        self.evet_name = "GameStart"
        self.left_deck = left_deck
        self.right_deck = right_deck

    def __str__(self):
        res = ""
        res = "{}!{}".format(self.evet_name,self.left_deck,self.right_deck)
        return res

class RoundStart(GameLogEntry):
    def __init__(self,left_deck, right_deck,left_hand,right_hand):
        self.evet_name = "RoundStart"
        self.left_deck = left_deck
        self.right_deck = right_deck
        self.left_hand = left_hand
        self.right_hand = right_hand
    
    def __str__(self):
        res = ""
        res = "{}!{}!{}!{}!{}".format(self.evet_name,self.left_deck,self.right_deck,self.left_hand,self.right_hand)
        return res

class CardAdded(GameLogEntry):
    def __init__(self,card, side_num):
        self.evet_name = "CardAdded"
        self.card = card
        self.side_num = side_num

    def __str__(self):
        res = ""
        res = "{}!{}!{}".format(self.evet_name,self.card,self.side_num)
        return res

class BoardState():
    def __init__(self):
         self.left_side = []
         self.right_side = []
         self.OnGameEvent = Event()

    def left_count(self):
        return len(self.left_side)
    
    def right_count(self):
        return len(self.right_side)
    
    def take_damage(self,card,damage):
        pre_state = str(self)
        pre_event = TakingDamage(pre_state,damage)
        self.OnGameEvent(pre_event)
        card.take_damage(damage)
        post_state = str(self)
        post_event = TookDamage(pre_state,damage,post_state)
        self.OnGameEvent(post_event)
    
    def buf_amount(self,card,amount):
        pre_state = str(self)
        pre_event = BuffingAmount(pre_state,amount)
        self.OnGameEvent(pre_event)
        card.buf_amount(amount)
        post_state = str(self)
        post_event = BuffedAmount(pre_state,amount,post_state)
        self.OnGameEvent(post_event)

    def set_stat(self,card,value):
        pre_state = str(self)
        pre_event = SettingStat(pre_state,value)
        self.OnGameEvent(pre_event)
        card.stat = value
        post_state = str(self)
        post_event = SetStat(pre_state,value,post_state)
        self.OnGameEvent(post_event)
       
         
    @staticmethod
    def create_card(stat, ability_num,suit):
        #side =  self.left_side if side_num ==0 else self.right_side
        card = Card(stat, Ability_List[ability_num],suit,0)
        return card

        
    def add_card(self,card,side_num):
        side =  self.left_side if side_num ==0 else self.right_side
        card.side_num = side_num
        pre_state = str(self)
        pre_event = DebutingCard(pre_state,card,side_num)
        self.OnGameEvent(pre_event)
        card.debut(self,side_num)
        side.append(card)
        post_state = str(self)
        post_event = DebutedCard(pre_state,card,side_num,post_state)
        self.OnGameEvent(post_event)

    def clean_side(self, side_num):
        side =  self.left_side if side_num ==0 else self.right_side
        self.clean_up()
         


    def kill_card(self, card):
        side = None
        side_num=-1
        not_found= False
        if card in self.left_side:
            side = self.left_side
            side_num = 0
        elif card in self.right_side:
            side = self.right_side
            side_num = 1
        else:
            not_found = True
        if not not_found:
            pre_state = str(self)
            pre_event = SwaningCard(pre_state,card,side_num)
            self.OnGameEvent(pre_event)
            card.swangsong(self,side_num)
            if card in side:
                side.remove(card)
            post_state = str(self)
            post_event = SwanedCard(pre_state,card,side_num,post_state)
            self.OnGameEvent(post_event)
           

    def clean_up(self):
        for card in self.left_side:
            if card.is_dead and card.swang_called:
                self.left_side.remove(card)
        for card in self.right_side:
            if card.is_dead and card.swang_called:
                self.right_side.remove(card)



    def perfomance(self):
        pre_state = str(self)
        left_card = self.left_side[0]
        pre_event = PreBattleCard(pre_state,left_card,0)
        self.OnGameEvent(pre_event)
        left_card.performance(self)
        post_state = str(self)
        post_event =PreBattleDone(pre_state,left_card,0,post_state)
        self.OnGameEvent(post_event)
       
        
        right_card = self.right_side[0]
        pre_state = str(self)
        pre_event = PreBattleCard(pre_state,right_card,1)
        self.OnGameEvent(pre_event)
        right_card.performance(self)
        post_state = str(self)
        post_event =PreBattleDone(pre_state,right_card,1,post_state)
        self.OnGameEvent(post_event)

        right_attack = right_card.stat
        left_attack = left_card.stat

        pre_state = str(self)
        left_card.take_damage(right_attack)
        right_card.take_damage(left_attack)
        post_state = str(self)

        post_event =PostBattle(pre_state,post_state)
        self.OnGameEvent(post_event)
        
        if left_card.is_dead:
            self.kill_card(left_card)
        #right card might have died as a result of swangsong    
        if right_card.is_dead and right_card in self.right_side:
            self.kill_card(right_card)
        self.clean_up()

    def AddSubscribersForLockGameEvent(self,objMethod):
        self.OnGameEvent += objMethod
         
    def RemoveSubscribersForGameEvent(self,objMethod):
        self.OnGameEvent -= objMethod

    def __str__(self):
        lc ='EMPTY' if len(self.left_side) == 0 else  str(self.left_side[0])
        rc ='EMPTY' if len(self.right_side) == 0 else  str(self.right_side[0])

        res = lc + '|||' + rc
        return res

class Event(object):
 
    def __init__(self):
        self.__eventhandlers = []
 
    def __iadd__(self, handler):
        self.__eventhandlers.append(handler)
        return self
 
    def __isub__(self, handler):
        self.__eventhandlers.remove(handler)
        return self
 
    def __call__(self, *args, **keywargs):
        for eventhandler in self.__eventhandlers:
            eventhandler(*args, **keywargs)

class GameEngine():
    def __init__(self, first_hand,second_hand,stats):
        self.board_state = BoardState()
        self.left_cards = []
        self.right_cards = []
        for card_num in first_hand:
            card = BoardState.create_card(stats[card_num][0],stats[card_num][1],stats[card_num][2])
            self.left_cards.append(card)
        
        for card_num in second_hand:
            card = BoardState.create_card(stats[card_num][0],stats[card_num][1],stats[card_num][2])
            self.right_cards.append(card)
        
        self.current_phaze = 0

    def return_winner(self):
        if len(self.board_state.left_side) > len(self.board_state.right_side):
            return -1 #left winner 
        elif len(self.board_state.left_side) < len(self.board_state.right_side):
            return 1 #right winner
        else:
            return 0 #draw
    
    def main_loop(self):
        round_list = []
        
        game_over = False
        logger.debug("---new game---")
        while not game_over:
            logger.debug("---new round---")
            logger.debug("--initial ---" + str(self.board_state))
            logger.debug("left hand:"+str(self.left_cards))
            logger.debug("right hand:"+str(self.right_cards))
            one_round = {}
            round_list.append(one_round)
            one_round["game_over"] = False
            one_round["phaze"] = self.current_phaze
            one_round["before"] = str(self.board_state)
            one_round["events"] = []
            start_event = RoundStart(str(self.left_cards),str(self.right_cards),str(self.board_state.left_side),str(self.board_state.right_side))
            one_round["events"].append(start_event)
            eventAppender = lambda event: one_round["events"].append(event)
            self.board_state.AddSubscribersForLockGameEvent(eventAppender)
            fight_worthy = self.board_state.left_count() > 0 and self.board_state.right_count() > 0
            enough_draw = len(self.left_cards)>0 and len(self.right_cards)>0
            if not enough_draw and not fight_worthy:
                game_over = True
                one_round["game_over"] = True   
                break
            if self.current_phaze == 0:
                logger.debug("---phaze 0---")
            
                if  enough_draw:
                    cardL = self.left_cards.pop()
                    card_event = CardAdded(cardL,0)
                    one_round["events"].append(card_event)
                    self.board_state.add_card(cardL,0)

                    cardR = self.right_cards.pop()
                    card_event = CardAdded(cardR,1)
                    one_round["events"].append(card_event)
                    self.board_state.add_card(cardR,1)

                self.current_phaze=1
            
            logger.debug("--play ---" + str(self.board_state))

            fight_worthy = self.board_state.left_count() > 0 and self.board_state.right_count() > 0


            if self.current_phaze==1 and fight_worthy:
                self.board_state.perfomance()
                self.current_phaze = 0
            
            logger.debug("--after ---" + str(self.board_state))
            self.board_state.RemoveSubscribersForGameEvent(eventAppender)
        return round_list 


Ability_List = []
Ability_List.append(BasicAbility())
Ability_List.append(MartyrdomAbility())
Ability_List.append(TokenAbility())
Ability_List.append(EaterAbility())
Ability_List.append(FighterAbility())
Ability_List.append(GrowerAbility())
Ability_List.append(DavidAbility())
Ability_List.append(InfestAbility())
Ability_List.append(ToxicAbility())