class PokerGame {
    constructor() {
        this.socket = null;
        this.username = '';
        this.gameState = null;
        this.isMyTurn = false;
        this.currentBetAmount = 0;
        
        this.initializeEventListeners();
        this.initializeSocket();
    }

    initializeEventListeners() {
        // Lobby events
        document.getElementById('joinGameBtn').addEventListener('click', () => this.joinGame());
        document.getElementById('usernameInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.joinGame();
        });

        // Add AI buttons
        document.getElementById('addEasyAI').addEventListener('click', () => this.addAI('Easy'));
        document.getElementById('addNormalAI').addEventListener('click', () => this.addAI('Normal'));
        document.getElementById('addHardAI').addEventListener('click', () => this.addAI('Hard'));

        // Start Game
        document.getElementById('startGameBtn').addEventListener('click', () => this.startGame());

        // Action buttons
        document.getElementById('foldBtn').addEventListener('click', () => this.fold());
        document.getElementById('checkCallBtn').addEventListener('click', () => this.checkCall());
        document.getElementById('betRaiseBtn').addEventListener('click', () => this.showBettingControls());

        // Betting controls
        document.getElementById('betSlider').addEventListener('input', (e) => this.updateBetDisplay(e.target.value));
        document.getElementById('confirmBet').addEventListener('click', () => this.placeBet());
        document.getElementById('cancelBet').addEventListener('click', () => this.hideBettingControls());

        // Preset bet buttons
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.setPresetBet(e.target.dataset.multiplier));
        });

        // Next hand button
        document.getElementById('nextHandBtn').addEventListener('click', () => this.nextHand());
    }

    initializeSocket() {
        this.socket = io();

        this.socket.on('connect', () => {
            this.addMessage('Connected to server');
        });

        this.socket.on('disconnect', () => {
            this.addMessage('Disconnected from server');
        });

        this.socket.on('game_state_update', (gameState) => {
            this.handleGameStateUpdate(gameState);
        });

        this.socket.on('error', (error) => {
            this.showError(error.message);
        });

        this.socket.on('game_over', (data) => {
            this.showWinnerModal(data.winners);
        });
    }

    joinGame() {
        const usernameInput = document.getElementById('usernameInput');
        this.username = usernameInput.value.trim();

        if (!this.username) {
            this.showError('Please enter a username');
            return;
        }

        this.socket.emit('join_game', { username: this.username });
        this.showGameScreen();
    }

    addAI(difficulty) {
        const aiName = `AI_${difficulty}_${Math.random().toString(36).substr(2, 5)}`;
        this.socket.emit('join_game', { username: aiName, isAI: true });
    }

    startGame() {
        this.socket.emit('start_game');
        document.getElementById('startGameBtn').style.display = 'none';
    }

    showGameScreen() {
        document.getElementById('lobby').classList.remove('active');
        document.getElementById('game').classList.add('active');
        document.getElementById('startGameBtn').style.display = 'block';
    }

    handleGameStateUpdate(gameState) {
        this.gameState = gameState;
        this.updateUI(gameState);
    }

    updateUI(gameState) {
        this.updatePhaseDisplay(gameState.phase);
        this.updatePotDisplay(gameState.pots);
        this.updatePlayers(gameState.players);
        this.updateCommunityCards(gameState.community_cards);
        this.updateActionPanel(gameState);
        this.updateLastAction(gameState.last_action);
    }

    updatePhaseDisplay(phase) {
        const phaseText = {
            'WAITING': 'WAITING FOR PLAYERS',
            'PREFLOP': 'PREFLOP',
            'FLOP': 'FLOP',
            'TURN': 'TURN', 
            'RIVER': 'RIVER',
            'SHOWDOWN': 'SHOWDOWN'
        }[phase] || phase;

        document.getElementById('phaseDisplay').textContent = phaseText;
    }

    updatePotDisplay(pots) {
        const mainPot = pots.find(pot => pot.name === 'Main Pot') || pots[0];
        const sidePots = pots.filter(pot => pot.name !== 'Main Pot');

        if (mainPot) {
            document.getElementById('mainPot').textContent = `Main Pot: $${mainPot.amount}`;
        }

        const sidePotsContainer = document.getElementById('sidePots');
        sidePotsContainer.innerHTML = '';

        sidePots.forEach((pot, index) => {
            const sidePotElement = document.createElement('div');
            sidePotElement.className = 'side-pot';
            sidePotElement.textContent = `${pot.name}: $${pot.amount}`;
            sidePotElement.title = `Eligible: ${pot.eligible_players.join(', ')}`;
            sidePotsContainer.appendChild(sidePotElement);
        });
    }

    // 修正: 自分の席を常に手前(seat-0)にするロジック
    updatePlayers(players) {
        // 1. まず全席をクリア
        document.querySelectorAll('.player-seat').forEach(seat => {
            seat.style.display = 'none';
            seat.classList.remove('active');
            const dealerBtn = seat.querySelector('.dealer-button');
            if(dealerBtn) dealerBtn.classList.remove('visible');
        });

        if (!players || players.length === 0) return;

        // 2. 自分のインデックスを探す
        const myIndex = players.findIndex(p => p.name === this.username);
        const playerCount = players.length;

        // 3. 各プレイヤーを表示
        players.forEach((player, serverIndex) => {
            // 自分の位置(myIndex)を0として、相対的な位置(offset)を計算
            // myIndexが-1(観戦者)の場合はそのまま
            let offset;
            if (myIndex !== -1) {
                offset = (serverIndex - myIndex + playerCount) % playerCount;
            } else {
                offset = serverIndex;
            }

            // 4. 相対位置を画面上の座席番号(seat-0～5)にマッピング
            // seat-0:下, seat-5:左下, seat-3:左上, seat-1:上, seat-2:右上, seat-4:右下
            // この順序で時計回りに配置する
            const seatMapping = [0, 5, 3, 1, 2, 4];
            
            // プレイヤー数が6人を超える場合は考慮が必要だが、今回は6人想定
            const displaySeatIndex = seatMapping[offset % 6];

            const seatElement = document.querySelector(`.player-seat.seat-${displaySeatIndex}`);
            if (seatElement) {
                this.updatePlayerSeat(seatElement, player);
            }
        });
    }

    updatePlayerSeat(seatElement, playerData) {
        if (!playerData || !playerData.name) return;

        seatElement.style.display = 'block';
        
        const infoElement = seatElement.querySelector('.player-info');
        const nameElement = seatElement.querySelector('.player-name');
        const stackElement = seatElement.querySelector('.player-stack');
        const betElement = seatElement.querySelector('.player-bet');
        const statusElement = seatElement.querySelector('.player-status');
        const cardsElement = seatElement.querySelector('.player-cards');
        const dealerButton = seatElement.querySelector('.dealer-button');

        nameElement.textContent = playerData.name;
        stackElement.textContent = `$${playerData.stack}`;
        betElement.textContent = playerData.bet_this_round > 0 ? `$${playerData.bet_this_round}` : '';

        statusElement.textContent = playerData.status === 'FOLDED' ? 'FOLD' : 
                                   playerData.status === 'ALL_IN' ? 'ALL-IN' : '';
        statusElement.style.display = playerData.status !== 'ACTIVE' ? 'block' : 'none';

        if (playerData.is_turn) {
            seatElement.classList.add('active');
            this.isMyTurn = playerData.name === this.username;
        }

        if (playerData.is_dealer) {
            dealerButton.classList.add('visible');
        }

        cardsElement.innerHTML = '';
        if (playerData.hand && playerData.hand.length > 0) {
            playerData.hand.forEach(card => {
                const cardElement = this.createCardElement(card, true);
                cardsElement.appendChild(cardElement);
            });
        } else if (playerData.status !== 'FOLDED') {
            for (let i = 0; i < 2; i++) {
                const cardBack = document.createElement('div');
                cardBack.className = 'card card-back';
                cardsElement.appendChild(cardBack);
            }
        }
    }

    createCardElement(cardData, isFaceUp = false) {
        const card = document.createElement('div');
        card.className = `card ${this.getSuitColor(cardData.suit)}`;
        
        if (isFaceUp) {
            card.innerHTML = `
                <div class="card-corner">
                    <div class="card-rank">${cardData.rank}</div>
                    <div class="card-suit">${this.getSuitSymbol(cardData.suit)}</div>
                </div>
                <div class="card-suit large">${this.getSuitSymbol(cardData.suit)}</div>
                <div class="card-corner bottom">
                    <div class="card-rank">${cardData.rank}</div>
                    <div class="card-suit">${this.getSuitSymbol(cardData.suit)}</div>
                </div>
            `;
        } else {
            card.className += ' card-back';
        }

        card.classList.add('dealt');
        return card;
    }

    getSuitSymbol(suit) {
        const symbols = {
            'hearts': '♥',
            'diamonds': '♦', 
            'clubs': '♣',
            'spades': '♠'
        };
        return symbols[suit] || '?';
    }

    getSuitColor(suit) {
        return suit === 'hearts' || suit === 'diamonds' ? 'red' : 'black';
    }

    updateCommunityCards(cards) {
        const container = document.getElementById('communityCards');
        container.innerHTML = '';

        cards.forEach(cardData => {
            const cardElement = this.createCardElement(cardData, true);
            container.appendChild(cardElement);
        });
    }

    updateActionPanel(gameState) {
        const actionPanel = document.getElementById('actionPanel');
        const checkCallBtn = document.getElementById('checkCallBtn');
        const betRaiseBtn = document.getElementById('betRaiseBtn');

        if (this.isMyTurn && gameState.phase !== 'SHOWDOWN') {
            actionPanel.style.display = 'block';

            const callAmount = gameState.current_bet - this.getMyCurrentBet();
            
            if (callAmount > 0) {
                checkCallBtn.textContent = `Call $${callAmount}`;
                betRaiseBtn.textContent = 'Raise';
            } else {
                checkCallBtn.textContent = 'Check';
                betRaiseBtn.textContent = 'Bet';
            }

            this.setupBettingControls(gameState);
        } else {
            actionPanel.style.display = 'none';
            this.hideBettingControls();
        }
    }

    getMyCurrentBet() {
        if (!this.gameState || !this.gameState.players) return 0;
        
        const myPlayer = this.gameState.players.find(p => p.name === this.username);
        return myPlayer ? myPlayer.bet_this_round : 0;
    }

    setupBettingControls(gameState) {
        const myPlayer = this.gameState.players.find(p => p.name === this.username);
        if (!myPlayer) return;

        const minRaise = gameState.min_raise;
        const maxBet = myPlayer.stack + this.getMyCurrentBet();
        const currentBet = Math.max(minRaise, this.currentBetAmount);

        const slider = document.getElementById('betSlider');
        slider.min = minRaise;
        slider.max = maxBet;
        slider.value = currentBet;

        document.getElementById('minBet').textContent = `$${minRaise}`;
        document.getElementById('maxBet').textContent = `$${maxBet}`;
        
        this.updateBetDisplay(currentBet);
    }

    updateBetDisplay(amount) {
        this.currentBetAmount = parseInt(amount);
        document.getElementById('currentBet').textContent = `$${amount}`;
        
        const betRaiseBtn = document.getElementById('betRaiseBtn');
        const callAmount = this.gameState.current_bet - this.getMyCurrentBet();
        
        if (callAmount > 0) {
            betRaiseBtn.textContent = `Raise to $${amount}`;
        } else {
            betRaiseBtn.textContent = `Bet $${amount}`;
        }
    }

    showBettingControls() {
        document.getElementById('bettingControls').style.display = 'block';
        document.querySelector('.action-buttons').style.display = 'none';
    }

    hideBettingControls() {
        document.getElementById('bettingControls').style.display = 'none';
        document.querySelector('.action-buttons').style.display = 'flex';
    }

    setPresetBet(multiplier) {
        const myPlayer = this.gameState.players.find(p => p.name === this.username);
        if (!myPlayer) return;

        let betAmount;
        
        if (multiplier === 'all') {
            betAmount = myPlayer.stack + this.getMyCurrentBet();
        } else {
            const totalPot = this.gameState.pots.reduce((sum, pot) => sum + pot.amount, 0);
            betAmount = Math.floor(totalPot * parseFloat(multiplier));
            betAmount = Math.max(betAmount, this.gameState.min_raise);
            betAmount = Math.min(betAmount, myPlayer.stack + this.getMyCurrentBet());
        }

        this.updateBetDisplay(betAmount);
        document.getElementById('betSlider').value = betAmount;
    }

    fold() {
        this.socket.emit('player_action', {
            action: 'fold',
            amount: null
        });
        this.isMyTurn = false;
    }

    checkCall() {
        const callAmount = this.gameState.current_bet - this.getMyCurrentBet();
        
        if (callAmount > 0) {
            this.socket.emit('player_action', {
                action: 'call',
                amount: null
            });
        } else {
            this.socket.emit('player_action', {
                action: 'check',
                amount: null
            });
        }
        
        this.isMyTurn = false;
    }

    placeBet() {
        const callAmount = this.gameState.current_bet - this.getMyCurrentBet();
        
        if (callAmount > 0) {
            this.socket.emit('player_action', {
                action: 'raise',
                amount: this.currentBetAmount
            });
        } else {
            this.socket.emit('player_action', {
                action: 'bet',
                amount: this.currentBetAmount
            });
        }

        this.hideBettingControls();
        this.isMyTurn = false;
    }

    updateLastAction(lastAction) {
        if (!lastAction) return;

        const message = `${lastAction.player_name} ${lastAction.action}${lastAction.amount ? ` $${lastAction.amount}` : ''}`;
        this.addMessage(message);
    }

    showWinnerModal(winners) {
        const modal = document.getElementById('winnerModal');
        const winnerList = document.getElementById('winnerList');
        
        winnerList.innerHTML = '';
        
        winners.forEach(winner => {
            const winnerItem = document.createElement('div');
            winnerItem.className = 'winner-item';
            winnerItem.innerHTML = `
                <h3>${winner.player}</h3>
                <p>Win: $${winner.amount}</p>
                <p>Hand: ${winner.hand}</p>
                <p>${winner.pot_name}</p>
            `;
            winnerList.appendChild(winnerItem);
        });

        modal.style.display = 'flex';
    }

    nextHand() {
        document.getElementById('winnerModal').style.display = 'none';
        this.socket.emit('start_game');
    }

    addMessage(message) {
        const messagesContainer = document.getElementById('gameMessages');
        const messageElement = document.createElement('div');
        messageElement.className = 'message';
        messageElement.textContent = message;
        
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showError(message) {
        alert(`Error: ${message}`);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new PokerGame();
});