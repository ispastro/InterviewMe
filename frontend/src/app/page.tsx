import Script from 'next/script';

const landingMarkup = `
<div class="bg-surface font-body text-on-surface selection:bg-primary selection:text-on-primary">
  <nav class="bg-[#070d1f]/60 backdrop-blur-xl border-b border-[#41475b]/20 shadow-[0_0_20px_rgba(132,85,239,0.15)] flex justify-between items-center w-full px-8 py-4 max-w-full docked full-width top-0 sticky z-50">
    <div class="flex items-center gap-8">
      <a href="/" class="text-2xl font-bold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-[#ba9eff] to-[#53ddfc] font-headline">InterviewMe</a>
      <div class="hidden md:flex gap-6 items-center">
        <a class="font-['Space_Grotesk'] tracking-wider uppercase text-sm font-bold text-[#53ddfc] border-b-2 border-[#53ddfc] pb-1" href="#">Platform</a>
        <a class="font-['Space_Grotesk'] tracking-wider uppercase text-sm font-bold text-[#dfe4fe]/70 hover:text-[#ba9eff] transition-all duration-300" href="#">Pathways</a>
        <a class="font-['Space_Grotesk'] tracking-wider uppercase text-sm font-bold text-[#dfe4fe]/70 hover:text-[#ba9eff] transition-all duration-300" href="#">Success Stories</a>
      </div>
    </div>
    <div class="flex items-center gap-4">
      <a href="/login" class="text-[#dfe4fe]/70 hover:text-[#ba9eff] transition-all duration-300 font-headline uppercase text-xs font-bold tracking-widest scale-95 active:scale-90 transition-transform">Log In</a>
      <a href="/register" class="intelligence-gradient text-on-primary-fixed px-6 py-2 rounded-lg font-headline uppercase text-xs font-bold tracking-widest shadow-[0_0_20px_rgba(132,85,239,0.3)] scale-95 active:scale-90 transition-transform">Get Started</a>
    </div>
  </nav>

  <main>
    <section class="relative min-h-[921px] flex flex-col items-center justify-center pt-24 pb-32 px-8 overflow-hidden">
      <div class="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_rgba(132,85,239,0.08),_transparent_70%)]"></div>
      <div class="relative z-10 max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
        <div class="space-y-10">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-outline-variant bg-surface-container-low">
            <span class="w-2 h-2 rounded-full bg-secondary animate-pulse"></span>
            <span class="text-[10px] font-headline font-bold uppercase tracking-[0.2em] text-secondary">Neural Simulation Engine v4.2</span>
          </div>
          <h1 class="font-headline text-5xl md:text-7xl font-bold tracking-tighter leading-[0.9] text-on-surface">Master the <br/><span class="bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary">High-Stakes</span> <br/>Conversation</h1>
          <p class="text-tertiary text-lg max-w-lg font-light leading-relaxed">Experience the world's most sophisticated AI interview coach. Upload your resume and start a simulation tailored to your next elite career move.</p>
          <div class="flex flex-col sm:flex-row items-center gap-4 max-w-md">
            <div class="relative w-full group">
              <div class="absolute inset-0 bg-gradient-to-r from-primary to-secondary rounded-lg blur opacity-20 group-focus-within:opacity-40 transition-opacity"></div>
              <div class="relative flex items-center bg-surface-container-lowest border-b border-outline-variant rounded-lg px-4 py-3">
                <span class="material-symbols-outlined text-outline mr-3" data-icon="upload_file"></span>
                <input class="bg-transparent border-none focus:ring-0 text-sm w-full font-label placeholder:text-outline" placeholder="Upload Resume (.pdf)" type="text"/>
              </div>
            </div>
            <a href="/interview/setup" class="intelligence-gradient text-on-primary-fixed w-full sm:w-auto whitespace-nowrap px-8 py-3.5 rounded-lg font-headline font-bold uppercase text-sm tracking-widest hover:brightness-110 transition-all text-center">Get Started</a>
          </div>
        </div>

        <div class="relative group">
          <div class="absolute -inset-4 bg-gradient-to-tr from-primary/10 to-secondary/10 rounded-[2rem] blur-3xl opacity-50"></div>
          <div class="relative glass-panel rounded-[2rem] border border-outline-variant/30 overflow-hidden shadow-2xl">
            <div class="ai-pulse w-full"></div>
            <div class="p-6 border-b border-outline-variant/20 flex justify-between items-center bg-surface-container-high/40">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                  <span class="material-symbols-outlined text-primary text-xl" data-icon="psychology"></span>
                </div>
                <div>
                  <p class="text-xs font-headline font-bold uppercase tracking-widest text-primary">Interviewer</p>
                  <p class="text-[10px] text-outline">Neural Core 07</p>
                </div>
              </div>
              <div class="flex gap-2">
                <div class="px-3 py-1 rounded bg-[#ff6e84]/10 border border-[#ff6e84]/20 flex items-center gap-2">
                  <div class="w-1.5 h-1.5 rounded-full bg-[#ff6e84]"></div>
                  <span class="text-[10px] font-bold text-[#ff6e84] uppercase tracking-wider">Live Analysis</span>
                </div>
              </div>
            </div>
            <div class="relative aspect-video">
              <img class="w-full h-full object-cover opacity-60 mix-blend-luminosity" alt="Cinematic close-up of a high-tech digital human avatar on a dark screen with floating data points and biometric scanners" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBVJF1AdT34RODfz7Jf8rhJMzt5FgZ5oycIg6XZnVEG-PYOygUIeMzrLvC46GLP6hasQke5eSufVTE8kxb-XpdAH9sFfFELUAtK04S23M63g6vA54NTaEkPd4DR3u_pk4g2KiiEAfhKv9ckqXIkO2nRJvTi3gyhdvfrbLH3P3Yh-NeCJP5rhO5TMuTnTxHKgcAD5LGbXfm6yPuLmD7pRVafaRLAUIs8xUnN9eQlyXdU6MqDG3Ydb5c4qzvkFr7rowizBDxroAUVGh8"/>
              <div class="absolute inset-0 bg-gradient-to-t from-surface to-transparent"></div>
              <div class="absolute bottom-6 right-6 p-4 glass-panel rounded-xl border border-outline-variant/40 text-center">
                <p class="text-[10px] font-headline font-bold uppercase tracking-[0.2em] text-secondary mb-1">Confidence Score</p>
                <p class="text-3xl font-headline font-bold text-on-surface">88<span class="text-sm font-light text-outline">%</span></p>
                <div class="w-16 h-1 bg-surface-container-low mt-2 rounded-full overflow-hidden"><div class="w-[88%] h-full intelligence-gradient"></div></div>
              </div>
              <div class="absolute top-6 left-6 space-y-3">
                <div class="glass-panel p-3 rounded-lg border-l-2 border-primary text-xs font-label text-on-surface shadow-xl max-w-[200px]">"Your tone is assertive. Good structural clarity."</div>
                <div class="glass-panel p-3 rounded-lg border-l-2 border-secondary text-xs font-label text-on-surface shadow-xl max-w-[200px] opacity-80 translate-x-4">"Elaborate more on the technical constraints of Project X."</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="py-20 border-t border-outline-variant/10 bg-surface-container-lowest">
      <div class="max-w-7xl mx-auto px-8">
        <div class="flex flex-col md:flex-row items-center justify-between gap-12 opacity-50 grayscale hover:grayscale-0 transition-all duration-700">
          <img alt="Google" class="h-8 md:h-10 invert" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDaK2f4ftu_ea-u-CgwJyzdMqZfDijRwo2YjsLtPOwcHtA8gzw9ZWdcZRF7vx-t-oBBd11Envh5_9Uq0rQQdwspRE8Sw8ZNQQt62CEK3kfJujse5JKO8cJcZAWZqXxutRqpsBaErfe6vQRq8kT-QkYy5giN4R9-aoZ9eZGl0zi7z4VavDG1m5iBcpNZaYJxd8EuYTVHkWzG3yRDG0gC6ceLVV6Ma3CuCxdDakcHprBaQn29wUgRYJx8uFjkMtJ1m8fTfCCqSANiL4M"/>
          <img alt="Amazon" class="h-8 md:h-10 invert" src="https://lh3.googleusercontent.com/aida-public/AB6AXuC_IT8j93vVucBujFG4i3olOmGWRuGSLrzqbbrcoS1orhxpySg_X8TQhXxZt08zdq9tqj7HtcSQrNkYHUHianH05glJIZGyD9cer5W9I57wvlZXMYVoEMwkmm4jErqw8oHxAZytEswIc1EeC-W6SpR7yLjjhKy6z3ehGniyprXnk_wpM8tDO6bFZwUh0Vom-HeX_BKgK7Ebg3j3ZmoaMCA8S3zEmxjTbGA0KdRDfd0n4OyNRXVNrjPna0hY_KoD16eKFpeligTLGGc"/>
          <img alt="Meta" class="h-8 md:h-10 invert" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBDlR_PTeAxw8y0tLlH2INpoJp-SEpthIfPDM2AG6lfmX3mhlAs-kMjvIDjHHT4XznxkJWH5P0kzMLNNGRfYpZRyilaWN2UbLePmiYbBbI75HefFCdfvmRus-hEt8hHRkuwWj4vCm5RDQgax5Hu_MDSBMWRs3OXmEpRYGOpdvxwVT1U2YOG8mZTRwfNFdElEDO0ZRPSyTBLU7GuD7be4Qsblf-Y16F7XVAcHZmFeOhHPXZj1AAPgqjnII-Y-mvbLQmR2tsomSJ3cLI"/>
          <img alt="Netflix" class="h-8 md:h-10 invert" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAYzxu73X0OcRNxFq1udL6cm_A4_9ROpGQUUUZqKrqpXUbW1_Wr-438IY4Cbv2PYr8THBpVSsOFdk_-VFO_bEjKPDT2fX38eaCuYv5I9A8i0_fpiH3qgC_GoXGjls0H2v3sX5gf2OpCc_BY_TT1NLg147v_L-9KhjaQ5eEVaf5xYNi1mlFB3lcccXuvs-XZLq4dPocC6etYUbpOkNUTzI3qVQ0HeW4p2T0hNsbpL2ckeGIGT9AzG8-i8KlcQzROfvCIKtFyvrqLJEM"/>
          <img alt="Stripe" class="h-8 md:h-10 invert" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAHtO3KuZszGedalBDr8kS-_YWM8T-ExzFSGpDxqpqJ1L8hyNFVTrxDgrd7yhj75Q0h9P45eynsXyD__FmI5d98oGvYCCeZthU20mwqpCAJ0_Oc7nRWe-clvOfDYuUkaI9SpK7TeXGTBwZXguH_ypq7HCQOskDL04W8rcDQZ0c7Qbi7ANmHUnC9npEimniCsk9gY456dnU9mdD6Uibxyb-o-2o8X0wxUNPmEf7_8lWcf5wVtKEyDesbhrBgtplbI2B2LmZfl023HXQ"/>
          <img alt="Tesla" class="h-8 md:h-10 invert" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCc9j3qA3xv9h5T_WculL81u52j868jjRSfRHvHsyQJC7w2Z3lC_oCOVxbxopON4FKJy_xAUB1yoPs40bYxLhGNun4N0vXOXOB-O6V0CgKf513TuVV6ynw6hAa5dDOZxAMqV5YGKrANQfyJO5oqDHrKbooVBSMRmt-0yuyXlLPR8U65kvHC1cxWks_zr0WYGnqE0ZUlo5x4Rdv4wa39rClcw2r0zZSmpp36vml4p-kgFWHkDLkJgYhYz6md4bju7bLLx51NJD9tjW0"/>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-10 mt-32">
          <div class="text-center group"><h3 class="text-5xl font-headline font-bold text-primary mb-2 group-hover:scale-110 transition-transform">14,200+</h3><p class="text-outline font-headline uppercase text-[10px] tracking-[0.3em]">Hires Secured</p></div>
          <div class="text-center group"><h3 class="text-5xl font-headline font-bold text-secondary mb-2 group-hover:scale-110 transition-transform">94%</h3><p class="text-outline font-headline uppercase text-[10px] tracking-[0.3em]">Success Rate</p></div>
          <div class="text-center group"><h3 class="text-5xl font-headline font-bold text-on-surface mb-2 group-hover:scale-110 transition-transform">$420M+</h3><p class="text-outline font-headline uppercase text-[10px] tracking-[0.3em]">Salary Increases</p></div>
        </div>
      </div>
    </section>

    <section class="py-40 px-8 relative overflow-hidden">
      <div class="absolute right-0 top-1/2 -translate-y-1/2 w-1/3 h-[500px] bg-primary/5 blur-[120px] rounded-full"></div>
      <div class="max-w-7xl mx-auto">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
          <div class="lg:col-span-5 space-y-8">
            <div class="label-md uppercase tracking-[0.4em] text-secondary font-headline font-bold text-xs">Simulated Reality</div>
            <h2 class="text-4xl md:text-5xl font-headline font-bold text-on-surface leading-tight">The Feedback Loop of Champions.</h2>
            <p class="text-tertiary text-lg font-light leading-relaxed">Our proprietary neural engine doesn't just ask questions-it analyzes micro-expressions, pacing, and keyword density in real-time to provide the same edge used by elite candidates at top-tier firms.</p>
            <div class="space-y-6 pt-4">
              <div class="flex items-start gap-4">
                <span class="material-symbols-outlined text-primary" data-icon="analytics"></span>
                <div><h4 class="text-on-surface font-headline font-bold">Semantic Depth Analysis</h4><p class="text-outline text-sm">We verify the weight of your answers against thousands of successful interview transcripts.</p></div>
              </div>
              <div class="flex items-start gap-4">
                <span class="material-symbols-outlined text-secondary" data-icon="speed"></span>
                <div><h4 class="text-on-surface font-headline font-bold">Sentiment Tracking</h4><p class="text-outline text-sm">Monitor your emotional resonance to ensure you're coming across as confident and approachable.</p></div>
              </div>
            </div>
          </div>
          <div class="lg:col-span-7">
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-4">
                <div class="glass-panel rounded-2xl border border-outline-variant/30 overflow-hidden">
                  <div class="p-4 border-b border-outline-variant/20 bg-surface-container-high/40 text-[10px] font-headline uppercase tracking-widest text-outline">AI Agent Perspective</div>
                  <div class="aspect-[4/5] relative">
                    <img class="w-full h-full object-cover" alt="High-tech glowing circuit board patterns with neon cyan and violet light streams on dark background" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDYVW3_RLONIdHeOZvVW-59kwLDgKvkKjw8cWZ-B5VNP7uNuNNu5f-g_xoSosERDwZemEyQfHxtZV0mgNrzWrrMNWr2Snhl1stPyu8L6sqvk6tOkGSZGroiNWCgXBDo9exV4d62WBwnTWGqLwzFpG2-tcjr5ygvTzyLtnEQ8U850D0ZVjaijDNTOnQ3Y8GoUKQ9xdIynenTi7L_yeZbZ7W88CjpdI-LO9GZfd7AYRwLYRrklTBNsUgUmEVysNGEqLNVF2CAo12tSG4"/>
                    <div class="absolute inset-0 bg-surface/40 flex items-center justify-center"><span class="material-symbols-outlined text-6xl text-secondary/40 animate-pulse" data-icon="voice_selection"></span></div>
                    <div class="absolute bottom-4 left-4 right-4"><div class="glass-panel p-4 rounded-xl border border-outline-variant/40"><div class="flex justify-between items-end mb-2"><span class="text-[8px] font-headline font-bold uppercase tracking-widest text-outline">Clarity</span><span class="text-xs font-headline font-bold text-secondary">92%</span></div><div class="h-1 bg-surface-container-low rounded-full overflow-hidden"><div class="h-full w-[92%] bg-secondary"></div></div></div></div>
                  </div>
                </div>
              </div>
              <div class="space-y-4 pt-12">
                <div class="glass-panel rounded-2xl border border-outline-variant/30 overflow-hidden">
                  <div class="p-4 border-b border-outline-variant/20 bg-surface-container-high/40 text-[10px] font-headline uppercase tracking-widest text-outline text-right">Candidate Simulation</div>
                  <div class="aspect-[4/5] relative">
                    <img class="w-full h-full object-cover grayscale brightness-75" alt="Professional young man in a modern office setting, looking at camera with a focused expression, soft cinematic lighting" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBNS9hyjpyfC8W8C6sqK41ANbZXdssRTyBTlPuOWQOczknT7_ZPO0HDXkd777aJXp33Lx1xg07pQZyFo6TtghLZ1lhFAPJh-6kfX2lt6hJRu72UFEyRSC5KJpV6707asF8RP3hb8JOT3rO5nghExRE5xIibJNMpU7hWwHCDIxS8CieerV83Eh4shT0d6AYft4dpWc63RExw7Y3G0Mx1wT9o_aIeoGf7Ot3S2rxhSSvqKP5hDyyxyRgWdXHks4zz9hQVfWQymk6kpFU"/>
                    <div class="absolute bottom-4 left-4 right-4"><div class="glass-panel p-4 rounded-xl border border-outline-variant/40"><div class="flex justify-between items-end mb-2"><span class="text-[8px] font-headline font-bold uppercase tracking-widest text-outline">Confidence</span><span class="text-xs font-headline font-bold text-primary">78%</span></div><div class="h-1 bg-surface-container-low rounded-full overflow-hidden"><div class="h-full w-[78%] bg-primary"></div></div></div></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="py-32 px-8 bg-surface-container-low">
      <div class="max-w-7xl mx-auto">
        <div class="text-center max-w-3xl mx-auto mb-24">
          <h2 class="text-4xl md:text-5xl font-headline font-bold text-on-surface mb-6">Engineered for Excellence.</h2>
          <p class="text-outline text-lg">Every module is crafted to dismantle a specific friction point in the career journey.</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="md:col-span-2 relative glass-panel rounded-3xl border border-outline-variant/20 p-10 overflow-hidden group">
            <div class="absolute top-0 right-0 p-12 opacity-10 group-hover:opacity-20 transition-opacity"><span class="material-symbols-outlined text-[180px] text-primary" data-icon="description"></span></div>
            <div class="relative z-10 max-w-md">
              <div class="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-8"><span class="material-symbols-outlined text-primary" data-icon="quick_reference_all"></span></div>
              <h3 class="text-3xl font-headline font-bold text-on-surface mb-4">Hyper-Personalized Resume Analysis</h3>
              <p class="text-outline leading-relaxed mb-6">We don't just check for keywords. We evaluate the strategic narrative of your career history to highlight untapped high-value experiences.</p>
              <a class="inline-flex items-center gap-2 text-primary font-headline font-bold uppercase text-xs tracking-widest hover:gap-4 transition-all" href="#">Analyze Now <span class="material-symbols-outlined text-sm" data-icon="arrow_forward"></span></a>
            </div>
          </div>
          <div class="relative bg-surface-container-highest rounded-3xl border border-outline-variant/20 p-10 overflow-hidden flex flex-col justify-end">
            <div class="absolute top-10 left-10 opacity-20"><span class="material-symbols-outlined text-6xl text-secondary" data-icon="dynamic_form"></span></div>
            <h3 class="text-2xl font-headline font-bold text-on-surface mb-4">Dynamic Scenarios</h3>
            <p class="text-outline text-sm leading-relaxed">AI-generated curveball questions based on your specific industry and level.</p>
          </div>
          <div class="relative bg-surface-container-highest rounded-3xl border border-outline-variant/20 p-10 overflow-hidden flex flex-col justify-end">
            <div class="absolute top-10 left-10 opacity-20"><span class="material-symbols-outlined text-6xl text-[#ff6e84]" data-icon="query_stats"></span></div>
            <h3 class="text-2xl font-headline font-bold text-on-surface mb-4">Delta Reports</h3>
            <p class="text-outline text-sm leading-relaxed">Deep analytics showing your growth trajectory across multiple simulation sessions.</p>
          </div>
          <div class="md:col-span-2 relative glass-panel rounded-3xl border border-outline-variant/20 p-10 overflow-hidden group">
            <div class="flex flex-col md:flex-row items-center gap-12">
              <div class="flex-1">
                <h3 class="text-3xl font-headline font-bold text-on-surface mb-4">Elite Pathway Coaching</h3>
                <p class="text-outline leading-relaxed">Step-by-step roadmaps for transitioning into FAANG, MBB, or top-tier private equity roles.</p>
              </div>
              <div class="w-full md:w-64 aspect-square bg-gradient-to-br from-[#8455ef]/20 to-[#40ceed]/20 rounded-2xl flex items-center justify-center border border-outline-variant/30"><span class="material-symbols-outlined text-7xl text-on-surface/30" data-icon="timeline"></span></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="py-40 px-8 relative">
      <div class="max-w-7xl mx-auto">
        <div class="flex flex-col items-center mb-32">
          <div class="label-md uppercase tracking-[0.4em] text-primary font-headline font-bold text-xs mb-6">The Process</div>
          <h2 class="text-4xl md:text-6xl font-headline font-bold text-on-surface text-center">Three Steps to Unstoppable.</h2>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-0 relative">
          <div class="hidden md:block absolute top-1/4 left-1/3 right-1/3 h-[1px] bg-gradient-to-r from-primary/30 via-secondary/30 to-primary/30 z-0"></div>
          <div class="relative z-10 flex flex-col items-center text-center p-8 group">
            <div class="w-20 h-20 intelligence-gradient rounded-2xl flex items-center justify-center mb-10 shadow-[0_0_30px_rgba(132,85,239,0.3)] group-hover:rotate-12 transition-transform duration-500"><span class="material-symbols-outlined text-on-primary-fixed text-4xl" data-icon="cloud_upload"></span></div>
            <h4 class="text-xl font-headline font-bold text-on-surface mb-4">Data Synthesis</h4>
            <p class="text-outline text-sm leading-relaxed max-w-xs">Upload your resume and the target job description. Our AI builds a custom behavioral profile.</p>
          </div>
          <div class="relative z-10 flex flex-col items-center text-center p-8 group">
            <div class="w-20 h-20 bg-surface-container-highest border border-outline-variant/40 rounded-2xl flex items-center justify-center mb-10 shadow-xl group-hover:-rotate-12 transition-transform duration-500"><span class="material-symbols-outlined text-secondary text-4xl" data-icon="model_training"></span></div>
            <h4 class="text-xl font-headline font-bold text-on-surface mb-4">AI Simulation</h4>
            <p class="text-outline text-sm leading-relaxed max-w-xs">Engage in an adaptive, vocal interview. The difficulty scales based on your real-time performance.</p>
          </div>
          <div class="relative z-10 flex flex-col items-center text-center p-8 group">
            <div class="w-20 h-20 bg-surface-container-highest border border-outline-variant/40 rounded-2xl flex items-center justify-center mb-10 shadow-xl group-hover:rotate-12 transition-transform duration-500"><span class="material-symbols-outlined text-primary text-4xl" data-icon="auto_awesome"></span></div>
            <h4 class="text-xl font-headline font-bold text-on-surface mb-4">Neural Feedback</h4>
            <p class="text-outline text-sm leading-relaxed max-w-xs">Receive a granular breakdown of your performance with actionable scripts to improve your impact.</p>
          </div>
        </div>
      </div>
    </section>

    <section class="py-40 px-8 relative">
      <div class="max-w-5xl mx-auto glass-panel rounded-[3rem] border border-outline-variant/20 p-16 text-center relative overflow-hidden">
        <div class="absolute -top-24 -right-24 w-64 h-64 bg-primary/10 blur-[100px] rounded-full"></div>
        <div class="absolute -bottom-24 -left-24 w-64 h-64 bg-secondary/10 blur-[100px] rounded-full"></div>
        <div class="relative z-10">
          <h2 class="text-5xl md:text-7xl font-headline font-bold text-on-surface mb-8 tracking-tighter leading-tight">Your Dream Role is <br/>a <span class="bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary">Conversation</span> Away.</h2>
          <p class="text-tertiary text-xl mb-12 max-w-2xl mx-auto font-light">Join the top 1% of candidates who use Intelligence to outpace the competition.</p>
          <div class="flex flex-col sm:flex-row items-center justify-center gap-6">
            <a href="/register" class="intelligence-gradient text-on-primary-fixed px-12 py-5 rounded-xl font-headline font-bold uppercase text-sm tracking-widest shadow-[0_0_40px_rgba(132,85,239,0.4)] hover:scale-105 transition-all">Unlock Full Access</a>
            <a href="#" class="px-12 py-5 rounded-xl border border-outline-variant/40 font-headline font-bold uppercase text-sm tracking-widest text-on-surface hover:bg-surface-container-high transition-all">View Pricing</a>
          </div>
          <p class="mt-12 text-outline text-[10px] font-headline uppercase tracking-[0.4em]">No Credit Card Required • Free Diagnostic Simulation</p>
        </div>
      </div>
    </section>
  </main>

  <footer class="bg-[#000000] w-full border-t border-[#41475b]/10 py-12">
    <div class="max-w-7xl mx-auto px-8 flex flex-col md:flex-row justify-between items-center gap-10">
      <div class="flex flex-col gap-4">
        <span class="font-['Space_Grotesk'] font-black text-[#dfe4fe] text-xl">InterviewMe</span>
        <p class="text-xs font-['Manrope'] tracking-wide text-[#6f758b]">© 2026 InterviewMe. Engineered for Excellence.</p>
      </div>
      <div class="flex flex-wrap justify-center gap-8">
        <a class="font-['Manrope'] text-xs tracking-wide text-[#6f758b] hover:text-[#ba9eff] transition-colors" href="#">Privacy Policy</a>
        <a class="font-['Manrope'] text-xs tracking-wide text-[#6f758b] hover:text-[#ba9eff] transition-colors" href="#">Terms of Service</a>
        <a class="font-['Manrope'] text-xs tracking-wide text-[#6f758b] hover:text-[#ba9eff] transition-colors" href="#">AI Ethics</a>
        <a class="font-['Manrope'] text-xs tracking-wide text-[#6f758b] hover:text-[#ba9eff] transition-colors" href="#">Careers</a>
      </div>
      <div class="flex gap-4">
        <div class="w-8 h-8 rounded-full border border-outline-variant/20 flex items-center justify-center group hover:border-primary transition-colors cursor-pointer"><span class="material-symbols-outlined text-sm text-[#6f758b] group-hover:text-primary" data-icon="language"></span></div>
        <div class="w-8 h-8 rounded-full border border-outline-variant/20 flex items-center justify-center group hover:border-secondary transition-colors cursor-pointer"><span class="material-symbols-outlined text-sm text-[#6f758b] group-hover:text-secondary" data-icon="share"></span></div>
      </div>
    </div>
  </footer>
</div>
`;

export default function LandingPage() {
  return (
    <>
      <Script
        src="https://cdn.tailwindcss.com?plugins=forms,container-queries"
        strategy="beforeInteractive"
      />
      <Script id="tailwind-config" strategy="beforeInteractive">
        {`
          tailwind.config = {
            darkMode: 'class',
            theme: {
              extend: {
                colors: {
                  primary: '#ba9eff',
                  secondary: '#53ddfc'
                },
                fontFamily: {
                  headline: ['Space Grotesk'],
                  body: ['Manrope'],
                  label: ['Manrope']
                }
              }
            }
          }
        `}
      </Script>
      <div
        className="dark"
        dangerouslySetInnerHTML={{ __html: landingMarkup }}
      />
    </>
  );
}
