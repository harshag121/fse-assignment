<!DOCTYPE html>

<html lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>MediSchedule MCP - Healthcare Assistant</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script id="tailwind-config">
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    colors: {
                        "primary": "#0d968b",
                        "background-light": "#f6f8f8",
                        "background-dark": "#102220",
                    },
                    fontFamily: {
                        "display": ["Inter", "sans-serif"]
                    },
                    borderRadius: {
                        "DEFAULT": "0.5rem",
                        "lg": "1rem",
                        "xl": "1.5rem",
                        "full": "9999px"
                    },
                },
            },
        }
    </script>
<style>
        body { font-family: 'Inter', sans-serif; }
        .material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24 }
    </style>
</head>
<body class="bg-background-light dark:bg-background-dark text-slate-900 dark:text-slate-100 font-display">
<div class="flex h-screen overflow-hidden">
<!-- Sidebar -->
<aside class="w-[280px] flex-shrink-0 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col">
<div class="p-6">
<div class="flex items-center gap-3 mb-8">
<div class="size-10 rounded-full bg-primary flex items-center justify-center text-white">
<span class="material-symbols-outlined">medical_services</span>
</div>
<div>
<h1 class="text-base font-bold leading-tight">MediSchedule MCP</h1>
<p class="text-xs text-slate-500 dark:text-slate-400">Healthcare Assistant</p>
</div>
</div>
<button class="w-full flex items-center justify-center gap-2 bg-primary hover:bg-primary/90 text-white font-semibold py-3 px-4 rounded-xl transition-colors mb-6 shadow-sm shadow-primary/20">
<span class="material-symbols-outlined text-[20px]">add_box</span>
<span>New Chat</span>
</button>
<nav class="space-y-1">
<p class="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Recent Chats</p>
<a class="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-primary/10 text-primary font-medium" href="#">
<span class="material-symbols-outlined text-[20px]">chat_bubble</span>
<span class="truncate text-sm">General Consult</span>
</a>
<a class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors" href="#">
<span class="material-symbols-outlined text-[20px]">chat_bubble</span>
<span class="truncate text-sm">Follow-up Dr. Smith</span>
</a>
<a class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors" href="#">
<span class="material-symbols-outlined text-[20px]">description</span>
<span class="truncate text-sm">Lab Results</span>
</a>
<a class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors" href="#">
<span class="material-symbols-outlined text-[20px]">vaccines</span>
<span class="truncate text-sm">Vaccination Record</span>
</a>
</nav>
</div>
<div class="mt-auto p-6 border-t border-slate-100 dark:border-slate-800">
<div class="flex items-center gap-3">
<div class="size-9 rounded-full bg-slate-200 dark:bg-slate-700" data-alt="User profile picture placeholder" style="background-image: url('https://lh3.googleusercontent.com/aida-public/AB6AXuBEISp5LL_qd_y8MKpLIZxpXACCujf_VGeiSamg0OgGDLE5mGq8udPwpZGMOQm3Sk_t261PEBKw9NlgPx3AZZnqnNlJH-HwdPIr1yeAdA6jTYLo89m28qcsOL0mq9UxzHzynfiUmarlMZBlEZDsAhL-zQb-2YUibsw88Y8vUdqo91ZcnY-ZVkBEwv3LwB2yFZUH_A17mQk6FAET0qi2a6-qBo9sjNTx2saELqIDLWZMY5nxf8GHYrbzlimZO1AdS1ErtciCu5Y2ZlcD')"></div>
<div class="flex-1 min-w-0">
<p class="text-sm font-semibold truncate">Alex Johnson</p>
<p class="text-xs text-slate-500 truncate">Premium Plan</p>
</div>
<span class="material-symbols-outlined text-slate-400 cursor-pointer">settings</span>
</div>
</div>
</aside>
<!-- Main Content -->
<main class="flex-1 flex flex-col relative overflow-hidden">
<!-- Header -->
<header class="h-16 flex-shrink-0 flex items-center justify-between px-6 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 z-10">
<div class="flex items-center gap-3">
<div class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary border border-primary/20">
<span class="material-symbols-outlined text-[18px]">calendar_today</span>
<span class="text-sm font-semibold tracking-tight">Booking with Dr. Ahuja</span>
</div>
</div>
<div class="flex items-center gap-2">
<button class="p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors">
<span class="material-symbols-outlined">info</span>
</button>
<button class="p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors">
<span class="material-symbols-outlined">more_vert</span>
</button>
</div>
</header>
<!-- Chat Area -->
<div class="flex-1 overflow-y-auto p-6 space-y-6">
<!-- AI Message -->
<div class="flex gap-4 max-w-2xl">
<div class="size-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 mt-1">
<span class="material-symbols-outlined text-primary text-[20px]">smart_toy</span>
</div>
<div class="space-y-1">
<p class="text-[11px] font-bold text-slate-400 uppercase tracking-widest ml-1">Assistant</p>
<div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl rounded-tl-none p-4 shadow-sm">
<p class="text-sm leading-relaxed">Hello! I can help you book an appointment with Dr. Ahuja. When would you like to visit?</p>
</div>
</div>
</div>
<!-- User Message -->
<div class="flex gap-4 max-w-2xl ml-auto flex-row-reverse">
<div class="size-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center flex-shrink-0 mt-1" data-alt="User avatar" style="background-image: url('https://lh3.googleusercontent.com/aida-public/AB6AXuCGZoPjoGvYqWmBZrMZXma2AfCYF1m4FGOTMfeodQeQQmLMxv1hkPluvYTUD826PhCy65urognIXhCrJJmqcnAzPs4mWSnZ92xJnHgPqMS3fz72YP-aCyT1MGLNlygSYvptWRiNKqa8RFqk5nZEYeJ_wLYWgUHn55rQ7TYRBkdKcAdEQtcA8l8imrdX3Yfe6_JD1SGof_GAEAxfO8LFwpiZ_B38fslzJarlIubvH6w19eybahY1Pfcuj8bN9CBvfADQi41EhlJlIG6U')"></div>
<div class="space-y-1 flex flex-col items-end">
<p class="text-[11px] font-bold text-slate-400 uppercase tracking-widest mr-1 text-right">You</p>
<div class="bg-primary text-white rounded-2xl rounded-tr-none p-4 shadow-sm">
<p class="text-sm leading-relaxed">I'm looking for an opening this Friday afternoon.</p>
</div>
</div>
</div>
<!-- AI Message with Loading Pill -->
<div class="flex gap-4 max-w-2xl">
<div class="size-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 mt-1">
<span class="material-symbols-outlined text-primary text-[20px]">smart_toy</span>
</div>
<div class="space-y-4">
<div class="space-y-1">
<p class="text-[11px] font-bold text-slate-400 uppercase tracking-widest ml-1">Assistant</p>
<div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl rounded-tl-none p-4 shadow-sm">
<p class="text-sm leading-relaxed">Checking Dr. Ahuja's schedule for Friday afternoon. One moment please...</p>
</div>
</div>
<!-- Loader Pill -->
<div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
<span class="material-symbols-outlined text-[18px] animate-spin text-primary">sync</span>
<span class="text-xs font-medium text-slate-600 dark:text-slate-300">Checking availability...</span>
</div>
</div>
</div>
</div>
<!-- Bottom Area -->
<div class="p-6 bg-gradient-to-t from-background-light dark:from-background-dark via-background-light/90 dark:via-background-dark/90 to-transparent">
<!-- Quick Actions -->
<div class="flex gap-2 mb-4">
<button class="flex items-center gap-2 px-4 py-2 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:border-primary/40 hover:text-primary transition-all shadow-sm">
<span class="material-symbols-outlined text-[16px]">event_available</span>
                        Check Availability
                    </button>
<button class="flex items-center gap-2 px-4 py-2 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:border-primary/40 hover:text-primary transition-all shadow-sm">
<span class="material-symbols-outlined text-[16px]">calendar_month</span>
                        My Appointments
                    </button>
</div>
<!-- Input Area -->
<div class="relative flex items-center gap-3">
<div class="flex-1 relative group">
<input class="w-full bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 rounded-full py-4 pl-6 pr-14 text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all shadow-sm" placeholder="Type your message..." type="text"/>
<button class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-primary transition-colors">
<span class="material-symbols-outlined">mic</span>
</button>
</div>
<button class="size-12 rounded-full bg-primary text-white flex items-center justify-center hover:bg-primary/90 transition-all shadow-lg shadow-primary/30 flex-shrink-0">
<span class="material-symbols-outlined">send</span>
</button>
</div>
<p class="text-center text-[10px] text-slate-400 mt-4">
                    MediSchedule MCP may provide information that should be verified with your healthcare provider.
                </p>
</div>
</main>
</div>
</body></html>