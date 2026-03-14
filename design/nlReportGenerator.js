<!DOCTYPE html>

<html lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
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
                    borderRadius: {"DEFAULT": "0.5rem", "lg": "1rem", "xl": "1.5rem", "full": "9999px"},
                },
            },
        }
    </script>
<style>
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }
    </style>
</head>
<body class="bg-background-light dark:bg-background-dark font-display text-slate-900 dark:text-slate-100 min-h-screen">
<div class="relative flex h-auto min-h-screen w-full flex-col group/design-root overflow-x-hidden">
<div class="layout-container flex h-full grow flex-col">
<!-- Header Component -->
<header class="flex items-center justify-between whitespace-nowrap border-b border-solid border-primary/10 px-6 md:px-20 py-4 bg-white dark:bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
<div class="flex items-center gap-3">
<div class="size-8 bg-primary rounded-lg flex items-center justify-center text-white">
<span class="material-symbols-outlined">analytics</span>
</div>
<h2 class="text-slate-900 dark:text-slate-100 text-lg font-bold leading-tight tracking-tight">PracticeInsight AI</h2>
</div>
<div class="flex flex-1 justify-end gap-4 items-center">
<button class="p-2 hover:bg-primary/10 rounded-full transition-colors">
<span class="material-symbols-outlined text-primary">notifications</span>
</button>
<div class="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 border-2 border-primary/20" data-alt="Professional headshot of a medical doctor" style='background-image: url("https://lh3.googleusercontent.com/aida-public/AB6AXuDcnKBV84OnhFHF2rYMu_qz80n69DlxnpCsSxDAMyFjIZTKT8MrFy-3DEDt0b0_j1j-JriHAlEe9szrRh7EMi5cNpLpUnQyjoaBjA8vRm3i5GKhbhxVYB23GVFc0jyfN_iovIMjVbuTv492bbPGT24F8vCfE4_iDQcsUSZvNPQ0DhDmDg2YHjl_g5sns1etYnXXNxtxXqMHmvYVvK5ynik7plyPEytx__k87ZAD5xfJCL_JYJWx0E72xbCM1QjRxS93TbOrwjCC0k9a");'></div>
</div>
</header>
<main class="px-4 md:px-20 flex flex-1 justify-center py-10">
<div class="layout-content-container flex flex-col max-w-[800px] flex-1 gap-8">
<!-- Hero Section -->
<div class="text-center space-y-2">
<h1 class="text-slate-900 dark:text-slate-100 tracking-tight text-4xl md:text-5xl font-extrabold leading-tight">Ask Your Practice</h1>
<p class="text-slate-500 dark:text-slate-400 text-lg">Generate instant clinical and operational reports using natural language.</p>
</div>
<!-- Main Input Area -->
<div class="flex flex-col gap-4 bg-white dark:bg-slate-900 p-6 rounded-xl border border-primary/10 shadow-sm">
<div class="relative flex flex-col">
<textarea class="form-input w-full min-h-[200px] resize-none rounded-lg text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-primary/50 border-primary/20 bg-background-light dark:bg-slate-800 placeholder:text-slate-400 text-lg font-normal p-5" placeholder="Ask anything about your practice..."></textarea>
<div class="absolute bottom-4 left-4 flex gap-2">
<button class="p-2 text-primary hover:bg-primary/10 rounded-lg transition-colors" title="Select Date Range">
<span class="material-symbols-outlined">calendar_today</span>
</button>
<button class="p-2 text-primary hover:bg-primary/10 rounded-lg transition-colors" title="Voice Input">
<span class="material-symbols-outlined">mic</span>
</button>
<button class="p-2 text-primary hover:bg-primary/10 rounded-lg transition-colors" title="Attach Document">
<span class="material-symbols-outlined">attach_file</span>
</button>
</div>
</div>
<!-- Suggestions -->
<div class="flex flex-wrap gap-2 py-2">
<span class="text-xs font-semibold uppercase tracking-wider text-slate-400 w-full mb-1">Try asking:</span>
<button class="flex h-9 items-center justify-center gap-x-2 rounded-full bg-primary/10 hover:bg-primary/20 border border-primary/20 px-4 transition-colors">
<span class="material-symbols-outlined text-sm text-primary">history</span>
<p class="text-primary text-sm font-medium">Yesterday's visits</p>
</button>
<button class="flex h-9 items-center justify-center gap-x-2 rounded-full bg-primary/10 hover:bg-primary/20 border border-primary/20 px-4 transition-colors">
<span class="material-symbols-outlined text-sm text-primary">thermostat</span>
<p class="text-primary text-sm font-medium">Patients with fever</p>
</button>
<button class="flex h-9 items-center justify-center gap-x-2 rounded-full bg-primary/10 hover:bg-primary/20 border border-primary/20 px-4 transition-colors">
<span class="material-symbols-outlined text-sm text-primary">event_busy</span>
<p class="text-primary text-sm font-medium">Cancellation rate</p>
</button>
</div>
<!-- Main Action -->
<div class="pt-2">
<button class="w-full flex cursor-pointer items-center justify-center gap-3 overflow-hidden rounded-xl h-14 px-5 bg-primary hover:bg-primary/90 text-white text-lg font-bold transition-all shadow-lg shadow-primary/20">
<span class="material-symbols-outlined">magic_button</span>
<span>Generate Report</span>
</button>
</div>
</div>
<!-- Results Section -->
<div class="flex flex-col gap-6 pt-6">
<div class="flex items-center justify-between">
<h3 class="text-xl font-bold text-slate-800 dark:text-slate-200">Latest Insights</h3>
<div class="flex gap-2">
<button class="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg hover:bg-slate-50 transition-colors text-sm font-medium">
<span class="material-symbols-outlined text-sm">picture_as_pdf</span>
                                    Download PDF
                                </button>
<button class="flex items-center gap-2 px-4 py-2 bg-[#4A154B] text-white rounded-lg hover:opacity-90 transition-colors text-sm font-medium">
<span class="material-symbols-outlined text-sm">send</span>
                                    Send to Slack
                                </button>
</div>
</div>
<!-- Sample Summary Card -->
<div class="bg-white dark:bg-slate-900 rounded-xl border border-primary/10 p-6 shadow-sm overflow-hidden relative">
<div class="absolute top-0 right-0 p-4">
<span class="px-2 py-1 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs font-bold rounded">+12% vs last week</span>
</div>
<div class="flex flex-col gap-6">
<div class="flex flex-col gap-1">
<p class="text-sm text-slate-500 dark:text-slate-400 font-medium">Weekly Patient Overview</p>
<h4 class="text-2xl font-bold">142 Total Consultations</h4>
</div>
<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
<div class="bg-background-light dark:bg-slate-800 p-4 rounded-lg">
<p class="text-xs text-slate-500 dark:text-slate-400 uppercase font-bold tracking-widest">Average Wait</p>
<p class="text-xl font-bold text-primary">14.5 min</p>
</div>
<div class="bg-background-light dark:bg-slate-800 p-4 rounded-lg">
<p class="text-xs text-slate-500 dark:text-slate-400 uppercase font-bold tracking-widest">Revenue Impact</p>
<p class="text-xl font-bold text-primary">$12,450</p>
</div>
<div class="bg-background-light dark:bg-slate-800 p-4 rounded-lg">
<p class="text-xs text-slate-500 dark:text-slate-400 uppercase font-bold tracking-widest">Follow-ups</p>
<p class="text-xl font-bold text-primary">38 cases</p>
</div>
</div>
<div class="space-y-3">
<p class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                                        Summary: The practice saw a significant increase in pediatric visits this week, specifically related to seasonal respiratory symptoms. Cancellation rates dropped to 4%, well below the monthly average.
                                    </p>
</div>
</div>
</div>
</div>
</div>
</main>
<!-- Footer -->
<footer class="py-10 text-center text-slate-400 text-sm">
<p>© 2024 PracticeInsight AI. HIPAA Compliant Analytics.</p>
</footer>
</div>
</div>
</body></html>