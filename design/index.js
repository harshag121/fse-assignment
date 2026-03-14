<!DOCTYPE html>

<html lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
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
        .mesh-gradient {
            background-color: #0d968b;
            background-image: 
                radial-gradient(at 0% 0%, #0d968b 0px, transparent 50%),
                radial-gradient(at 100% 0%, #ccfbf1 0px, transparent 50%),
                radial-gradient(at 100% 100%, #14b8a6 0px, transparent 50%),
                radial-gradient(at 0% 100%, #f0fdfa 0px, transparent 50%);
        }
    </style>
</head>
<body class="font-display bg-background-light dark:bg-background-dark text-slate-900 dark:text-slate-100 antialiased overflow-x-hidden">
<div class="relative min-h-screen flex flex-col">
<!-- Top Navigation -->
<header class="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-background-dark/80 backdrop-blur-md border-b border-primary/10">
<div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
<div class="flex items-center gap-2.5">
<div class="bg-primary p-1.5 rounded-lg flex items-center justify-center">
<span class="material-symbols-outlined text-white text-xl">smart_toy</span>
</div>
<span class="text-xl font-bold tracking-tight text-slate-900 dark:text-white">MedSched <span class="text-primary">AI</span></span>
</div>
<nav class="hidden md:flex items-center gap-8">
<a class="text-sm font-semibold text-slate-600 dark:text-slate-400 hover:text-primary transition-colors" href="#">Features</a>
<a class="text-sm font-semibold text-slate-600 dark:text-slate-400 hover:text-primary transition-colors" href="#">Security</a>
<a class="text-sm font-semibold text-slate-600 dark:text-slate-400 hover:text-primary transition-colors" href="#">Pricing</a>
</nav>
<div class="flex items-center gap-4">
<button class="hidden sm:block text-sm font-bold text-slate-700 dark:text-slate-300">Log in</button>
<button class="bg-primary text-white px-5 py-2 rounded-lg text-sm font-bold shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all">
                        Get Started
                    </button>
</div>
</div>
</header>
<!-- Main Hero & Selection Section -->
<main class="flex-grow pt-24 pb-16 flex items-center justify-center mesh-gradient">
<div class="max-w-5xl w-full px-6 flex flex-col items-center">
<!-- Hero Content -->
<div class="text-center mb-12 animate-fade-in">
<div class="mb-6 inline-flex items-center gap-2 bg-white/30 dark:bg-white/10 backdrop-blur-sm px-4 py-1.5 rounded-full border border-white/40">
<span class="material-symbols-outlined text-primary text-lg">verified</span>
<span class="text-xs font-bold uppercase tracking-widest text-primary">Next-Gen Patient Management</span>
</div>
<h1 class="text-4xl md:text-6xl font-black text-slate-900 dark:text-white leading-[1.1] mb-6 tracking-tight">
                        AI-Powered <br/>Medical Scheduling
                    </h1>
<p class="text-lg md:text-xl text-slate-700 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
                        Natural language appointment booking with MCP-powered intelligence. Seamlessly bridging the gap between healthcare providers and patients.
                    </p>
</div>
<!-- Split-Choice Cards -->
<div class="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl">
<!-- Patient Path -->
<div class="group relative bg-white dark:bg-slate-900/50 backdrop-blur-xl p-8 rounded-xl border border-white/50 dark:border-slate-800 shadow-2xl hover:shadow-primary/10 transition-all duration-300 cursor-pointer overflow-hidden">
<div class="absolute -top-12 -right-12 w-32 h-32 bg-primary/10 rounded-full group-hover:scale-150 transition-transform duration-500"></div>
<div class="relative z-10">
<div class="w-14 h-14 bg-primary/10 rounded-xl flex items-center justify-center mb-6 group-hover:bg-primary group-hover:text-white transition-colors">
<span class="material-symbols-outlined text-3xl">patient_list</span>
</div>
<h3 class="text-2xl font-bold text-slate-900 dark:text-white mb-3">I'm a Patient</h3>
<p class="text-slate-600 dark:text-slate-400 mb-8 leading-relaxed">
                                Book appointments using natural language. Speak or type to find the best slot with your specialist instantly.
                            </p>
<button class="flex items-center gap-2 text-primary font-bold group-hover:gap-3 transition-all">
<span>Book an Appointment</span>
<span class="material-symbols-outlined">arrow_forward</span>
</button>
</div>
</div>
<!-- Doctor Path -->
<div class="group relative bg-white dark:bg-slate-900/50 backdrop-blur-xl p-8 rounded-xl border border-white/50 dark:border-slate-800 shadow-2xl hover:shadow-primary/10 transition-all duration-300 cursor-pointer overflow-hidden">
<div class="absolute -top-12 -right-12 w-32 h-32 bg-primary/10 rounded-full group-hover:scale-150 transition-transform duration-500"></div>
<div class="relative z-10">
<div class="w-14 h-14 bg-primary/10 rounded-xl flex items-center justify-center mb-6 group-hover:bg-primary group-hover:text-white transition-colors">
<span class="material-symbols-outlined text-3xl">stethoscope</span>
</div>
<h3 class="text-2xl font-bold text-slate-900 dark:text-white mb-3">I'm a Doctor</h3>
<p class="text-slate-600 dark:text-slate-400 mb-8 leading-relaxed">
                                View detailed patient reports and practice analytics. Optimize your schedule with AI-driven workload balance.
                            </p>
<button class="flex items-center gap-2 text-primary font-bold group-hover:gap-3 transition-all">
<span>Access Provider Portal</span>
<span class="material-symbols-outlined">arrow_forward</span>
</button>
</div>
</div>
</div>
<!-- Hero Illustration Placeholder -->
<div class="mt-16 w-full max-w-lg aspect-video rounded-xl overflow-hidden border border-white/20 shadow-2xl bg-slate-800 relative">
<img alt="Medical AI Dashboard" class="w-full h-full object-cover opacity-80" data-alt="Friendly futuristic medical robot helping a doctor with scheduling on a screen" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDcNK3p15EmBhLjUCDEHc60beqiJsT0XV0JrrhLf96aYjdHIch8hVu5HmqOUSpO9TEueBHW2hsQVKAFe99X33ZEDe5ZiCPkIpXgul9Gbk7W-eCke-jW32NgpzIoqUHPDc-M4-JPZrFcOrUg1OpeWkThS2t3-IEdcKGHfolQTMralfkdWjTYtSfT2A9qyKfoaBGht1LN2RPNt1lN95vJQz0wfyanKVqW5y02lhdG2VLkNqKw-MGv_JQU7-j6JmRwOfc5xiFt39jacB7P"/>
<div class="absolute inset-0 bg-gradient-to-t from-background-dark/60 to-transparent"></div>
<div class="absolute bottom-4 left-4 right-4 text-white p-4">
<div class="flex items-center gap-3">
<div class="size-2 rounded-full bg-emerald-400 animate-pulse"></div>
<span class="text-xs font-medium tracking-widest uppercase">AI Engine Status: Active</span>
</div>
</div>
</div>
</div>
</main>
<!-- Footer -->
<footer class="bg-white dark:bg-background-dark py-12 border-t border-primary/5">
<div class="max-w-7xl mx-auto px-6">
<div class="flex flex-col md:flex-row justify-between items-center gap-8">
<div class="flex items-center gap-2.5 opacity-60 grayscale">
<div class="bg-slate-400 p-1 rounded-md flex items-center justify-center">
<span class="material-symbols-outlined text-white text-sm">smart_toy</span>
</div>
<span class="text-lg font-bold tracking-tight text-slate-900 dark:text-white">MedSched AI</span>
</div>
<div class="flex flex-wrap justify-center gap-8">
<a class="text-sm text-slate-500 dark:text-slate-400 hover:text-primary transition-colors" href="#">Privacy Policy</a>
<a class="text-sm text-slate-500 dark:text-slate-400 hover:text-primary transition-colors" href="#">Terms of Service</a>
<a class="text-sm text-slate-500 dark:text-slate-400 hover:text-primary transition-colors" href="#">HIPAA Compliance</a>
<a class="text-sm text-slate-500 dark:text-slate-400 hover:text-primary transition-colors" href="#">Contact Support</a>
</div>
<p class="text-sm text-slate-400 dark:text-slate-600">© 2024 MedSched AI. All rights reserved.</p>
</div>
</div>
</footer>
</div>
</body></html>