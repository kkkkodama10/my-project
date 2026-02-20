window.addEventListener('load', () => {
    connectWS()
})


function log(msg) {
    const status = document.getElementById('status')
    status.textContent = msg
}

let __ws = null
let __wsReconnectTimer = null
function connectWS() {
    // avoid multiple simultaneous connections
    if (__ws) return
    __ws = new WebSocket('ws://localhost:8000/ws?event_id=demo')
    __ws.onopen = () => {
        console.log('ws open')
        log('WS connected')
        // optional: send a hello
        try { __ws.send('hello from client') } catch (e) { console.debug(e) }
        // clear any pending reconnect attempts
        if (__wsReconnectTimer) { clearTimeout(__wsReconnectTimer); __wsReconnectTimer = null }
    }
    __ws.onmessage = (ev) => {
        // try to parse JSON messages (structured events). If it's plain text from server
        // (like an echo), ignore it in the UI to avoid noise.
        let parsed = null
        try {
            parsed = JSON.parse(ev.data)
        } catch (e) {
            // non-JSON text (e.g. server echo) — ignore for UI
            console.debug('ws text:', ev.data)
            return
        }
        console.log('ws msg', parsed)
        if (parsed.type === 'question.shown') {
            log('question shown')
            try { fetchState() } catch (e) { console.debug(e) }
        } else {
            // handle other structured events here
            log('ws event: ' + parsed.type)
            // for a set of server events, refresh state so UI transitions
            if (parsed.type === 'question.revealed' || parsed.type === 'event.state_changed' || parsed.type === 'question.closed') {
                try { fetchState() } catch (e) { console.debug(e) }
            }
            if (parsed.type === 'event.finished') {
                try { fetchState(); fetchResults() } catch (e) { console.debug(e) }
            }
        }
    }
    __ws.onclose = () => { log('WS closed'); __ws = null; /* attempt reconnect after delay */ __wsReconnectTimer = setTimeout(connectWS, 1500) }
    __ws.onerror = (e) => { console.error(e); log('WS error') }
}


// ----------------- Admin UI handlers -----------------

// Admin phase state machine:
//   waiting        -> Start enabled
//   started        -> Next, Finish enabled
//   question_shown -> Close, Finish enabled
//   question_closed -> Reveal, Finish enabled
//   question_revealed -> Next, Finish enabled
//   finished       -> all disabled
let adminPhase = 'waiting'
let adminCurrentQuestionId = null

function setAdminPhase(phase) {
    adminPhase = phase
    updateAdminButtons()
}

function updateAdminButtons() {
    const btns = {
        start:  document.getElementById('btn-start'),
        next:   document.getElementById('btn-next'),
        close:  document.getElementById('btn-close'),
        reveal: document.getElementById('btn-reveal'),
        finish: document.getElementById('btn-finish'),
    }
    // disable all first
    Object.values(btns).forEach(b => { if (b) b.disabled = true })
    switch (adminPhase) {
        case 'waiting':
            if (btns.start) btns.start.disabled = false
            break
        case 'started':
        case 'question_revealed':
            if (btns.next) btns.next.disabled = false
            if (btns.finish) btns.finish.disabled = false
            break
        case 'question_shown':
            if (btns.close) btns.close.disabled = false
            if (btns.finish) btns.finish.disabled = false
            break
        case 'question_closed':
            if (btns.reveal) btns.reveal.disabled = false
            if (btns.finish) btns.finish.disabled = false
            break
        case 'finished':
            // all stay disabled
            break
    }
}

async function adminLogin() {
    const pass = document.getElementById('admin-password').value
    const statusEl = document.getElementById('admin-login-status')
    try {
        const res = await fetch('http://localhost:8000/admin/login', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ password: pass })
        })
        if (!res.ok) throw new Error('login failed')
        statusEl.textContent = 'logged in'
        document.getElementById('admin-login').style.display = 'none'
        document.getElementById('admin-controls').style.display = 'block'
        updateAdminButtons()
    } catch (e) {
        statusEl.textContent = 'login error: ' + e.message
    }
}

async function adminAction(path, method = 'POST', body = null) {
    const status = document.getElementById('admin-action-status')
    try {
        const res = await fetch('http://localhost:8000' + path, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: body ? JSON.stringify(body) : undefined,
        })
        const data = await res.json()
        status.textContent = JSON.stringify(data)
        fetchAdminLogs()
        return data
    } catch (e) {
        status.textContent = 'error: ' + e.message
        return null
    }
}

function bindAdminUI() {
    document.getElementById('admin-login-btn').addEventListener('click', adminLogin)
    document.getElementById('btn-start').addEventListener('click', async () => {
        const data = await adminAction('/admin/events/demo/start')
        if (data && data.status === 'ok') setAdminPhase('started')
    })
    document.getElementById('btn-next').addEventListener('click', async () => {
        const data = await adminAction('/admin/events/demo/questions/next')
        if (data) {
            if (data.state === 'finished') {
                setAdminPhase('finished')
            } else if (data.question_id) {
                adminCurrentQuestionId = data.question_id
                setAdminPhase('question_shown')
            }
        }
    })
    document.getElementById('btn-close').addEventListener('click', async () => {
        if (!adminCurrentQuestionId) return
        const data = await adminAction(`/admin/events/demo/questions/${encodeURIComponent(adminCurrentQuestionId)}/close`)
        if (data && data.status === 'ok') setAdminPhase('question_closed')
    })
    document.getElementById('btn-reveal').addEventListener('click', async () => {
        if (!adminCurrentQuestionId) return
        const data = await adminAction(`/admin/events/demo/questions/${encodeURIComponent(adminCurrentQuestionId)}/reveal`)
        if (data && data.status === 'ok') setAdminPhase('question_revealed')
    })
    document.getElementById('btn-finish').addEventListener('click', async () => {
        const data = await adminAction('/admin/events/demo/finish')
        if (data && data.status === 'ok') setAdminPhase('finished')
    })
    document.getElementById('btn-reset').addEventListener('click', async () => {
        const data = await adminAction('/admin/events/demo/reset')
        if (data && data.status === 'ok') setAdminPhase('waiting')
    })
}

window.addEventListener('load', () => {
    bindAdminUI()
    updateAdminButtons()
})


// ----------------- Admin logs ----------------
async function fetchAdminLogs() {
    try {
        const res = await fetch('http://localhost:8000/admin/logs?limit=200', { credentials: 'include' })
        if (!res.ok) throw new Error('cannot fetch logs')
        const data = await res.json()
        const el = document.getElementById('admin-log-list')
        if (!el) return
        el.innerHTML = ''
        data.reverse().forEach(entry => {
            const d = document.createElement('div')
            d.textContent = `${entry.ts} ${entry.action} ${entry.event_id || ''} ${JSON.stringify(entry.payload || {})}`
            d.style.borderBottom = '1px solid #f0f0f0'
            d.style.padding = '4px 2px'
            el.appendChild(d)
        })
    } catch (e) { console.debug('fetchAdminLogs error', e) }
}

// ----------------- User flow ----------------
let currentQuestion = null
let choiceTimerInterval = null
let lastSelectedChoice = null
let deadlineReachedHandled = false

async function joinEvent() {
    const code = document.getElementById('join-code').value
    const status = document.getElementById('join-status')
    try {
        const res = await fetch('http://localhost:8000/events/demo/join', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify({ join_code: code })
        })
        if (!res.ok) throw new Error('join failed')
        const data = await res.json()
        status.textContent = 'joined'
        document.getElementById('register-section').style.display = 'block'
        document.getElementById('join-section').style.display = 'none'
    } catch (e) { status.textContent = 'error: ' + e.message }
}

async function registerUser() {
    const base = document.getElementById('display-base').value
    const status = document.getElementById('register-status')
    try {
        const res = await fetch('http://localhost:8000/events/demo/users/register', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify({ display_name_base: base })
        })
        if (!res.ok) throw new Error('register failed')
        const data = await res.json()
        status.textContent = 'registered: ' + data.user.display_name
        document.getElementById('play-section').style.display = 'block'
        document.getElementById('register-section').style.display = 'none'
        fetchState()
    } catch (e) { status.textContent = 'error: ' + e.message }
}

async function fetchState() {
    try {
        const res = await fetch('http://localhost:8000/events/demo/me/state', { credentials: 'include' })
        if (!res.ok) throw new Error('state fetch failed')
        const data = await res.json()
        renderState(data)
    } catch (e) { console.debug('fetchState', e) }
}

function renderState(data) {
    const me = data.me
    const meEl = document.getElementById('me-info')
    if (meEl) meEl.textContent = me ? `me: ${me.display_name}` : 'not registered'
    const qEl = document.getElementById('user-question')
    const choicesEl = document.getElementById('choices')
    const answerStatus = document.getElementById('answer-status')
    const timerElParent = document.getElementById('current-question-area')
    let timerEl = document.getElementById('deadline-timer')
    if (choicesEl) choicesEl.innerHTML = ''
    if (answerStatus) answerStatus.textContent = ''
    // remove existing timer interval if any
    if (choiceTimerInterval) { clearInterval(choiceTimerInterval); choiceTimerInterval = null }
    if (!timerEl) {
        timerEl = document.createElement('div')
        timerEl.id = 'deadline-timer'
        if (timerElParent) timerElParent.appendChild(timerEl)
    }

    if (data.current_question) {
        currentQuestion = data.current_question
        if (qEl) qEl.textContent = currentQuestion.question_text || JSON.stringify(currentQuestion)

        const deadlineISO = (data.event && data.event.answer_deadline_at) || null
        const deadline = deadlineISO ? new Date(deadlineISO) : null
        const now = new Date()
        const disabledByDeadline = deadline ? now > deadline : false
        const alreadyAnswered = !!data.my_answer
        const isRevealed = currentQuestion.correct_choice_index != null
        const correctIdx = currentQuestion.correct_choice_index

            ; (currentQuestion.choices || []).forEach(c => {
                const b = document.createElement('button')
                b.classList.add('choice-btn')
                b.textContent = c.text
                b.dataset.choiceIndex = c.choice_index

                // all buttons disabled after deadline, answer, or reveal
                if (disabledByDeadline || alreadyAnswered || isRevealed) {
                    b.classList.add('choice-disabled')
                    b.disabled = true
                } else {
                    b.addEventListener('click', () => {
                        markSelectedChoice(c.choice_index)
                        submitAnswer(currentQuestion.question_id, c.choice_index)
                    })
                }
                // mark user's answer
                if (data.my_answer && data.my_answer.choice_index === c.choice_index) {
                    b.classList.add('choice-selected')
                    lastSelectedChoice = c.choice_index
                }
                // after reveal: highlight correct / incorrect
                if (isRevealed) {
                    if (c.choice_index === correctIdx) {
                        b.classList.add('choice-correct')
                    } else if (data.my_answer && data.my_answer.choice_index === c.choice_index) {
                        b.classList.add('choice-incorrect')
                    }
                }
                choicesEl.appendChild(b)
            })

        // start countdown timer if deadline exists
        if (deadline) {
            deadlineReachedHandled = false
            const updateTimer = () => {
                const now = new Date()
                const diff = Math.max(0, Math.floor((deadline - now) / 1000))
                const mins = Math.floor(diff / 60)
                const secs = diff % 60
                timerEl.textContent = `締切: ${mins}:${secs.toString().padStart(2, '0')}`
                if (diff <= 0) {
                    Array.from(choicesEl.querySelectorAll('button')).forEach(btn => {
                        btn.disabled = true
                        btn.classList.add('choice-disabled')
                    })
                    if (!deadlineReachedHandled) {
                        deadlineReachedHandled = true
                        try { fetchState() } catch (e) { console.debug('fetchState after deadline failed', e) }
                    }
                    clearInterval(choiceTimerInterval)
                    choiceTimerInterval = null
                }
            }
            updateTimer()
            choiceTimerInterval = setInterval(updateTimer, 1000)
        } else {
            timerEl.textContent = ''
        }
    } else {
        if (qEl) qEl.textContent = 'no question'
    }
    // Reset handled flag when no question
    if (!data.current_question) deadlineReachedHandled = false

    // status messages
    if (answerStatus) {
        const isRevealed = data.current_question && data.current_question.correct_choice_index != null
        const deadlinePassed = data.event && data.event.answer_deadline_at && new Date() > new Date(data.event.answer_deadline_at)
        if (isRevealed && data.my_answer) {
            if (data.my_answer.is_correct) {
                answerStatus.textContent = '正解!'
                answerStatus.className = 'status-correct'
            } else {
                answerStatus.textContent = '不正解...'
                answerStatus.className = 'status-incorrect'
            }
        } else if (isRevealed && !data.my_answer) {
            answerStatus.textContent = '未回答'
            answerStatus.className = 'status-noanswer'
        } else if (deadlinePassed && data.my_answer) {
            answerStatus.textContent = '回答受付終了 — あなたの回答は送信済みです'
            answerStatus.className = 'status-closed'
        } else if (deadlinePassed && !data.my_answer) {
            answerStatus.textContent = '回答受付終了'
            answerStatus.className = 'status-closed'
        } else if (data.my_answer) {
            answerStatus.textContent = '回答済み — 結果発表をお待ちください'
            answerStatus.className = ''
        }
    }

    // show results section when event is finished
    const resultsSection = document.getElementById('results-section')
    const questionArea = document.getElementById('current-question-area')
    if (data.event && data.event.state === 'finished') {
        if (questionArea) questionArea.style.display = 'none'
        if (resultsSection) resultsSection.style.display = 'block'
        fetchResults()
    } else {
        if (questionArea) questionArea.style.display = 'block'
        if (resultsSection) resultsSection.style.display = 'none'
    }
}

async function submitAnswer(question_id, choice_index) {
    const status = document.getElementById('answer-status')
    try {
        const res = await fetch(`http://localhost:8000/events/demo/questions/${encodeURIComponent(question_id)}/answers`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify({ choice_index })
        })
        if (res.status === 409) { if (status) status.textContent = '回答受け付けられません（既に確定）'; return }
        const data = await res.json()
        if (status) {
            status.textContent = '回答を送信しました'
        }
        // refresh state to get authoritative info
        await fetchState()
    } catch (e) { if (status) status.textContent = 'error: ' + e.message }
}

function markSelectedChoice(choice_index) {
    const choicesEl = document.getElementById('choices')
    if (!choicesEl) return
    Array.from(choicesEl.querySelectorAll('button')).forEach(b => {
        if (String(b.dataset.choiceIndex) === String(choice_index)) {
            b.classList.add('choice-selected')
        } else {
            b.classList.remove('choice-selected')
        }
    })
    lastSelectedChoice = choice_index
}

async function fetchResults() {
    try {
        const res = await fetch('http://localhost:8000/events/demo/results', { credentials: 'include' })
        if (!res.ok) throw new Error('results fetch failed')
        const data = await res.json()
        renderResults(data)
    } catch (e) { console.debug('fetchResults', e) }
}

function renderResults(data) {
    const tbody = document.querySelector('#results-table tbody')
    if (!tbody) return
    tbody.innerHTML = ''
    ;(data.leaderboard || []).forEach(entry => {
        const tr = document.createElement('tr')
        const cells = [
            entry.rank,
            entry.display_name,
            entry.correct_count,
            (entry.accuracy * 100).toFixed(0) + '%',
            entry.correct_time_sum_sec_1dp + 's',
        ]
        cells.forEach(val => {
            const td = document.createElement('td')
            td.textContent = val
            tr.appendChild(td)
        })
        tbody.appendChild(tr)
    })
    const summaryEl = document.getElementById('event-summary')
    if (summaryEl && data.event_summary) {
        summaryEl.textContent = `全${data.event_summary.total_questions}問 / 終了: ${data.event_summary.finished_at || '-'}`
    }
}

function bindUserUI() {
    const j = document.getElementById('btn-join')
    const r = document.getElementById('btn-register')
    if (j) j.addEventListener('click', joinEvent)
    if (r) r.addEventListener('click', registerUser)
}

window.addEventListener('load', () => {
    bindUserUI()
    fetchState()
    fetchAdminLogs()
})
