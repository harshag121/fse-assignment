<!DOCTYPE html>

<html lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Doctor Analytics Dashboard</title>
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
                "display": ["Inter"]
              },
              borderRadius: {"DEFAULT": "0.5rem", "lg": "1rem", "xl": "1.5rem", "full": "9999px"},
            },
          },
        }
    </script>
<style>
        body { font-family: 'Inter', sans-serif; }
        .material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
    </style>
</head>
<body class="bg-background-light dark:bg-background-dark text-slate-900 dark:text-slate-100 min-h-screen">
<div class="flex h-screen overflow-hidden">
<!-- Sidebar Navigation -->
<aside class="w-64 flex-shrink-0 border-r border-primary/10 bg-white dark:bg-background-dark/50 hidden lg:flex flex-col">
<div class="p-6 flex items-center gap-3">
<div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
<span class="material-symbols-outlined">health_and_safety</span>
</div>
<h2 class="font-bold text-lg tracking-tight">MedAnalytics</h2>
</div>
<nav class="flex-1 px-4 space-y-2 mt-4">
<a class="flex items-center gap-3 px-4 py-3 rounded-xl bg-primary text-white" href="#">
<span class="material-symbols-outlined">dashboard</span>
<span class="font-medium">Dashboard</span>
</a>
<a class="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-primary/5 transition-colors" href="#">
<span class="material-symbols-outlined text-slate-500">calendar_today</span>
<span class="font-medium">Appointments</span>
</a>
<a class="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-primary/5 transition-colors" href="#">
<span class="material-symbols-outlined text-slate-500">group</span>
<span class="font-medium">Patients</span>
</a>
<a class="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-primary/5 transition-colors" href="#">
<span class="material-symbols-outlined text-slate-500">description</span>
<span class="font-medium">Reports</span>
</a>
<a class="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-primary/5 transition-colors" href="#">
<span class="material-symbols-outlined text-slate-500">settings</span>
<span class="font-medium">Settings</span>
</a>
</nav>
<div class="p-4 border-t border-primary/10">
<div class="flex items-center gap-3 p-2 bg-primary/5 rounded-xl">
<div class="w-10 h-10 rounded-full bg-cover" data-alt="Professional portrait of Dr. Ahuja" style="background-image: url('https://lh3.googleusercontent.com/aida-public/AB6AXuDGdIJ3vXZfwCYqD1rGva_DaOF94DcCKbkW6S60FjBS0iAHaN2cN-c9esIJAHsvbmH8g5Dsm_T4peKr497LACpf5uyeIfQXn8DmtotS7bC7es-z3VE6gIwyQDGwD4rTE4omc-ZgyRJxHVhzwxHw3aoPtB3g80vh1Hak2AxFWaPcPZ1RlN7Iony8YwzyFbhJ74qWGy43rcI0cHojk9qFafTP7Rs5Vl5ydw30UR3zFqV9lCpcAaGHklZiaqKs9WL5YEnBni9PoWIdtlE6')"></div>
<div class="flex flex-col">
<span class="text-sm font-bold">Dr. Ahuja</span>
<span class="text-xs text-slate-500">General Practitioner</span>
</div>
</div>
</div>
</aside>
<!-- Main Content -->
<main class="flex-1 overflow-y-auto scroll-smooth">
<!-- Header -->
<header class="sticky top-0 z-10 bg-background-light/80 dark:bg-background-dark/80 backdrop-blur-md px-8 py-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
<div>
<h1 class="text-2xl font-bold tracking-tight">Good morning, Dr. Ahuja</h1>
<p class="text-slate-500 dark:text-slate-400">Here is what's happening with your practice today.</p>
</div>
<div class="flex items-center gap-4">
<div class="relative group">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">search</span>
<input class="pl-10 pr-4 py-2 bg-white dark:bg-background-dark border border-primary/10 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none w-64" placeholder="Search patients..." type="text"/>
</div>
<button class="bg-primary hover:bg-primary/90 text-white px-6 py-2 rounded-xl font-bold transition-all shadow-lg shadow-primary/20 flex items-center gap-2">
<span class="material-symbols-outlined text-sm">download</span>
                        Generate Report
                    </button>
</div>
</header>
<div class="p-8 space-y-8">
<!-- Stats Grid -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
<div class="bg-white dark:bg-background-dark/40 p-6 rounded-xl border border-primary/5 shadow-sm">
<div class="flex justify-between items-start mb-4">
<span class="p-2 bg-primary/10 rounded-lg text-primary material-symbols-outlined">event_available</span>
<span class="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">+12%</span>
</div>
<h3 class="text-slate-500 text-sm font-medium mb-1">Today's Appointments</h3>
<p class="text-3xl font-bold">8</p>
</div>
<div class="bg-white dark:bg-background-dark/40 p-6 rounded-xl border border-primary/5 shadow-sm">
<div class="flex justify-between items-start mb-4">
<span class="p-2 bg-amber-100 rounded-lg text-amber-600 material-symbols-outlined">pending_actions</span>
<span class="text-xs font-bold text-slate-400 bg-slate-50 px-2 py-1 rounded-full">0%</span>
</div>
<h3 class="text-slate-500 text-sm font-medium mb-1">Pending Confirmations</h3>
<p class="text-3xl font-bold">3</p>
</div>
<div class="bg-white dark:bg-background-dark/40 p-6 rounded-xl border border-primary/5 shadow-sm">
<div class="flex justify-between items-start mb-4">
<span class="p-2 bg-indigo-100 rounded-lg text-indigo-600 material-symbols-outlined">group</span>
<span class="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">+8%</span>
</div>
<h3 class="text-slate-500 text-sm font-medium mb-1">Patients This Week</h3>
<p class="text-3xl font-bold">24</p>
</div>
<div class="bg-white dark:bg-background-dark/40 p-6 rounded-xl border border-primary/5 shadow-sm">
<div class="flex justify-between items-start mb-4">
<span class="p-2 bg-rose-100 rounded-lg text-rose-600 material-symbols-outlined">cancel</span>
<span class="text-xs font-bold text-rose-600 bg-rose-50 px-2 py-1 rounded-full">-5%</span>
</div>
<h3 class="text-slate-500 text-sm font-medium mb-1">Cancelled</h3>
<p class="text-3xl font-bold">2</p>
</div>
</div>
<!-- Charts and Lists Grid -->
<div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
<!-- Line Chart Section -->
<div class="xl:col-span-2 bg-white dark:bg-background-dark/40 p-8 rounded-xl border border-primary/5 shadow-sm">
<div class="flex justify-between items-center mb-8">
<h3 class="font-bold text-lg">Appointment Volume</h3>
<select class="bg-transparent border-none text-sm font-medium text-slate-500 focus:ring-0 cursor-pointer">
<option>Last 7 Days</option>
<option>Last 30 Days</option>
</select>
</div>
<div class="relative h-64 w-full">
<svg class="w-full h-full" preserveaspectratio="none" viewbox="0 0 100 40">
<defs>
<lineargradient id="chartGradient" x1="0" x2="0" y1="0" y2="1">
<stop offset="0%" stop-color="#0d968b" stop-opacity="0.2"></stop>
<stop offset="100%" stop-color="#0d968b" stop-opacity="0"></stop>
</lineargradient>
</defs>
<path d="M0,35 Q10,10 20,25 T40,15 T60,30 T80,10 T100,20 L100,40 L0,40 Z" fill="url(#chartGradient)"></path>
<path d="M0,35 Q10,10 20,25 T40,15 T60,30 T80,10 T100,20" fill="none" stroke="#0d968b" stroke-linecap="round" stroke-width="1.5"></path>
</svg>
<div class="absolute bottom-0 left-0 right-0 flex justify-between text-[10px] text-slate-400 font-bold uppercase tracking-wider pt-4">
<span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
</div>
</div>
</div>
<!-- Donut Chart Section -->
<div class="bg-white dark:bg-background-dark/40 p-8 rounded-xl border border-primary/5 shadow-sm">
<h3 class="font-bold text-lg mb-8">Status Distribution</h3>
<div class="relative flex items-center justify-center h-48 mb-8">
<!-- CSS-only Donut Mockup -->
<div class="w-40 h-40 rounded-full border-[16px] border-slate-100 dark:border-slate-800 relative">
<div class="absolute inset-[-16px] rounded-full border-[16px] border-primary border-t-transparent border-l-transparent transform rotate-45"></div>
<div class="absolute inset-0 flex flex-col items-center justify-center">
<span class="text-3xl font-bold">88%</span>
<span class="text-[10px] uppercase font-bold text-slate-400">Confirmed</span>
</div>
</div>
</div>
<div class="space-y-3">
<div class="flex items-center justify-between text-sm">
<div class="flex items-center gap-2">
<div class="w-3 h-3 rounded-full bg-primary"></div>
<span class="text-slate-500">Confirmed</span>
</div>
<span class="font-bold">68</span>
</div>
<div class="flex items-center justify-between text-sm">
<div class="flex items-center gap-2">
<div class="w-3 h-3 rounded-full bg-amber-400"></div>
<span class="text-slate-500">Pending</span>
</div>
<span class="font-bold">12</span>
</div>
<div class="flex items-center justify-between text-sm">
<div class="flex items-center gap-2">
<div class="w-3 h-3 rounded-full bg-rose-400"></div>
<span class="text-slate-500">Cancelled</span>
</div>
<span class="font-bold">2</span>
</div>
</div>
</div>
</div>
<!-- Footer Section Grid -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-8 pb-12">
<!-- Recent Activity -->
<div class="bg-white dark:bg-background-dark/40 p-8 rounded-xl border border-primary/5 shadow-sm">
<div class="flex justify-between items-center mb-6">
<h3 class="font-bold text-lg">Recent Activity</h3>
<button class="text-primary text-sm font-semibold hover:underline">View All</button>
</div>
<div class="space-y-6">
<div class="flex gap-4">
<div class="w-10 h-10 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
<span class="material-symbols-outlined">check_circle</span>
</div>
<div class="flex-1">
<p class="text-sm font-medium">Appointment confirmed with <span class="font-bold">Sarah Jenkins</span></p>
<p class="text-xs text-slate-400 mt-1">10 minutes ago</p>
</div>
</div>
<div class="flex gap-4">
<div class="w-10 h-10 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
<span class="material-symbols-outlined">schedule</span>
</div>
<div class="flex-1">
<p class="text-sm font-medium">New appointment request from <span class="font-bold">Robert Fox</span></p>
<p class="text-xs text-slate-400 mt-1">45 minutes ago</p>
</div>
</div>
<div class="flex gap-4">
<div class="w-10 h-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
<span class="material-symbols-outlined">description</span>
</div>
<div class="flex-1">
<p class="text-sm font-medium">Lab report uploaded for <span class="font-bold">Eleanor Pena</span></p>
<p class="text-xs text-slate-400 mt-1">2 hours ago</p>
</div>
</div>
</div>
</div>
<!-- Quick Actions -->
<div class="bg-white dark:bg-background-dark/40 p-8 rounded-xl border border-primary/5 shadow-sm">
<h3 class="font-bold text-lg mb-6">Quick Actions</h3>
<div class="grid grid-cols-2 gap-4">
<button class="flex flex-col items-center justify-center gap-3 p-6 rounded-xl border border-primary/10 hover:bg-primary/5 transition-all group">
<span class="material-symbols-outlined text-primary group-hover:scale-110 transition-transform">mail</span>
<span class="text-sm font-medium">Send Daily Summary</span>
</button>
<button class="flex flex-col items-center justify-center gap-3 p-6 rounded-xl border border-primary/10 hover:bg-primary/5 transition-all group">
<span class="material-symbols-outlined text-primary group-hover:scale-110 transition-transform">add_task</span>
<span class="text-sm font-medium">New Prescription</span>
</button>
<button class="flex flex-col items-center justify-center gap-3 p-6 rounded-xl border border-primary/10 hover:bg-primary/5 transition-all group">
<span class="material-symbols-outlined text-primary group-hover:scale-110 transition-transform">event</span>
<span class="text-sm font-medium">Reschedule Day</span>
</button>
<button class="flex flex-col items-center justify-center gap-3 p-6 rounded-xl border border-primary/10 hover:bg-primary/5 transition-all group">
<span class="material-symbols-outlined text-primary group-hover:scale-110 transition-transform">support_agent</span>
<span class="text-sm font-medium">Contact Staff</span>
</button>
</div>
</div>
</div>
</div>
</main>
</div>
</body></html>