// Слова приходят из views.py через JSON
const words = window.STUDY_WORDS;

let currentIndex = 0;
let correctCount = 0;

// Для хранения состояния букв для каждого слова
const wordStates = {};

// DOM элементы
const translateDiv = document.getElementById('puzzle-translate');
const slotsDiv = document.getElementById('puzzle-slots');
const lettersDiv = document.getElementById('puzzle-letters');
const progressDiv = document.getElementById('puzzle-progress');
const timerDiv = document.getElementById('timer');
const scoreDiv = document.getElementById('score');
const clearBtn = document.getElementById('clear-btn');

// Таймер
let seconds = 0;
const timerInterval = setInterval(() => {
    seconds++;
    const m = String(Math.floor(seconds / 60)).padStart(2,'0');
    const s = String(seconds % 60).padStart(2,'0');
    timerDiv.innerText = `${m}:${s}`;
}, 1000);

// Инициализация слова
function showWord() {
    const wordObj = words[currentIndex];
    const word = wordObj.word;

    translateDiv.innerText = wordObj.main_translation;

    // Прогресс
    progressDiv.innerText = `${currentIndex+1} / ${words.length}`;

    // Создаем слоты
    slotsDiv.innerHTML = '';
    for(let i=0;i<word.length;i++){
        const span = document.createElement('span');
        if(wordStates[word]?.slots?.[i]){
            span.innerText = wordStates[word].slots[i];
            if(wordStates[word].slots[i] === word[i]){
                span.classList.add('correct');
            }
        }
        slotsDiv.appendChild(span);
    }

    // Создаем буквы для выбора
    lettersDiv.innerHTML = '';
    const shuffled = shuffleArray(word.split(''));
    shuffled.forEach(ch => {
        const span = document.createElement('span');
        span.innerText = ch;
        if(wordStates[word]?.used?.includes(ch)){
            span.classList.add('used');
        }
        span.onclick = () => selectLetter(ch);
        lettersDiv.appendChild(span);
    });
}

// Выбор буквы
function selectLetter(ch){
    const word = words[currentIndex].word;
    const state = wordStates[word] || {slots: [], used: []};
    // ставим букву в первый пустой слот
    const emptyIndex = state.slots.findIndex(s => !s);
    if(emptyIndex === -1) return;
    state.slots[emptyIndex] = ch;
    state.used.push(ch);
    wordStates[word] = state;
    showWord();
    checkAnswer();
}

// Проверка правильности
function checkAnswer(){
    const word = words[currentIndex].word;
    const state = wordStates[word];
    if(!state) return;

    if(state.slots.join('') === word){
        // подсветка
        const spans = slotsDiv.querySelectorAll('span');
        spans.forEach((s,i)=>s.classList.add('correct'));
        // увеличиваем score если первый раз
        if(!state.completed){
            correctCount++;
            scoreDiv.innerText = `${correctCount} / ${words.length}`;
            state.completed = true;
        }
    }
}

// Очистить
clearBtn.onclick = () => {
    const word = words[currentIndex].word;
    wordStates[word] = {slots: [], used: []};
    showWord();
}

// Навигация
function nextWord(){
    if(currentIndex < words.length-1) currentIndex++;
    showWord();
}
function prevWord(){
    if(currentIndex > 0) currentIndex--;
    showWord();
}

// Завершение
function finishStudy(){
    clearInterval(timerInterval);
    alert(`Вы завершили изучение. Правильных: ${correctCount} / ${words.length}`);
}

// Вспомогательные функции
function shuffleArray(array){
    return array.sort(()=>Math.random()-0.5);
}

// Инициализация
showWord();
