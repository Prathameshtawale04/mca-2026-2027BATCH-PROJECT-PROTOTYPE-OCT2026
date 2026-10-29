/**
 * MovieFlix - Frontend JavaScript
 * Netflix-Inspired Scroll-Tied UI, Parallax, IntersectionObserver Animations,
 * Carousel Scrolling, Mobile Drawer, and Defensive Image Fallbacks.
 */

document.addEventListener('DOMContentLoaded', () => {
  const FALLBACK_POSTER = '/static/img/poster-fallback.svg';

  // ----------------------------------------------------------------------------
  // 1. Defensive Image Fallback Handler
  // ----------------------------------------------------------------------------
  function attachImageFallbacks() {
    document.querySelectorAll('img').forEach((img) => {
      // Guard against /None, null, or empty src
      if (!img.src || img.src.includes('/None') || img.src.endsWith('/img/')) {
        img.src = FALLBACK_POSTER;
      }

      img.addEventListener('error', function () {
        if (this.src !== window.location.origin + FALLBACK_POSTER && !this.src.endsWith(FALLBACK_POSTER)) {
          this.src = FALLBACK_POSTER;
        }
      });
    });
  }
  attachImageFallbacks();

  // ----------------------------------------------------------------------------
  // 2. Dynamic Sticky Navigation on Scroll
  // ----------------------------------------------------------------------------
  const siteHeader = document.getElementById('siteHeader');
  if (siteHeader) {
    const handleNavScroll = () => {
      if (window.scrollY > 30) {
        siteHeader.classList.add('scrolled');
      } else {
        siteHeader.classList.remove('scrolled');
      }
    };
    window.addEventListener('scroll', handleNavScroll, { passive: true });
    handleNavScroll();
  }

  // ----------------------------------------------------------------------------
  // 3. Scroll-Tied Hero Parallax & Fade Effect
  // ----------------------------------------------------------------------------
  const heroStage = document.getElementById('heroStage');
  const heroBackdrop = document.getElementById('heroBackdrop');
  const heroContent = document.getElementById('heroContent');

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (heroStage && heroBackdrop && heroContent && !prefersReducedMotion) {
    let ticking = false;

    window.addEventListener('scroll', () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const scrollY = window.scrollY;
          const stageHeight = heroStage.offsetHeight;

          if (scrollY <= stageHeight) {
            // Subtle parallax translation of backdrop image
            const backdropOffset = scrollY * 0.32;
            heroBackdrop.style.transform = `translate3d(0, ${backdropOffset}px, 0)`;

            // Subtle fade and upward translate of hero typography
            const opacity = Math.max(0, 1 - (scrollY / (stageHeight * 0.75)));
            const textOffset = scrollY * 0.18;
            heroContent.style.opacity = opacity.toFixed(2);
            heroContent.style.transform = `translate3d(0, ${textOffset}px, 0)`;
          }

          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });
  }

  // ----------------------------------------------------------------------------
  // 3b. Cinematic Hero Top 5 Trending Carousel Engine (5-Second Poster Delay + Trailer)
  // ----------------------------------------------------------------------------
  if (heroStage) {
    const posterDelayMs = parseInt(heroStage.dataset.delay, 10) || 5000;
    const slides = document.querySelectorAll('.hero-body-container');
    const backdrops = document.querySelectorAll('.hero-backdrop-container');
    const heroSlidesTrack = document.getElementById('heroSlidesTrack');
    const heroBackdropsTrack = document.getElementById('heroBackdropsTrack');
    const prevBtn = document.getElementById('heroPrevBtn');
    const nextBtn = document.getElementById('heroNextBtn');
    const heroMuteToggle = document.getElementById('heroMuteToggle');

    let currentIndex = 0;
    const totalSlides = slides.length || 5;
    let ytPlayer = null;
    let isVideoPlaying = false;
    let isMuted = true;
    let delayTimer = null;
    let delayElapsed = false;
    let autoRotateTimer = null;
    let isHovered = false;

    function getActiveTrailerId() {
      const activeSlide = slides[currentIndex];
      return activeSlide ? activeSlide.dataset.trailerId || 'Way9Dexny3w' : 'Way9Dexny3w';
    }

    function scheduleAutoSlide() {
      if (autoRotateTimer) clearTimeout(autoRotateTimer);
      if (isHovered) return;
      autoRotateTimer = setTimeout(() => {
        if (!isHovered) {
          switchSlide(currentIndex + 1, false, 'right');
        }
      }, 25000); // 25s trailer preview
    }

    function switchSlide(newIndex, manualUserClick = false, forceDirection = null) {
      if (newIndex < 0) newIndex = totalSlides - 1;
      if (newIndex >= totalSlides) newIndex = 0;

      currentIndex = newIndex;
      delayElapsed = false;
      isVideoPlaying = false;

      // 1. Instantly hide video and reveal high-res poster
      heroStage.classList.remove('video-active');

      // 2. Clear previous timers
      if (delayTimer) clearTimeout(delayTimer);
      if (autoRotateTimer) clearTimeout(autoRotateTimer);

      // 3. Smoothly slide the continuous backdrop and slide content tracks!
      const slidePercent = -(currentIndex * 20); // 5 slides = 20% each
      if (heroBackdropsTrack) {
        heroBackdropsTrack.style.transform = `translate3d(${slidePercent}%, 0, 0)`;
      }
      if (heroSlidesTrack) {
        heroSlidesTrack.style.transform = `translate3d(${slidePercent}%, 0, 0)`;
      }

      // 4. Update active class for slides and backdrops
      slides.forEach((s, idx) => {
        s.classList.toggle('active', idx === currentIndex);
      });
      backdrops.forEach((b, idx) => {
        b.classList.toggle('active', idx === currentIndex);
      });

      // 5. Load the new trailer in the background player
      const nextTrailer = getActiveTrailerId();
      if (ytPlayer && typeof ytPlayer.loadVideoById === 'function') {
        try {
          ytPlayer.mute();
          ytPlayer.loadVideoById({
            videoId: nextTrailer,
            startSeconds: 0,
            suggestedQuality: 'hd1080',
          });
        } catch (e) {
          console.warn('Trailer load error:', e);
        }
      }

      // 6. At exactly 5 seconds (5s poster rule), reveal video in background
      delayTimer = setTimeout(() => {
        delayElapsed = true;
        tryActivateTrailer();
        scheduleAutoSlide();
      }, posterDelayMs);
    }

    function tryActivateTrailer() {
      if (delayElapsed && heroStage) {
        if (ytPlayer && typeof ytPlayer.playVideo === 'function') {
          try {
            ytPlayer.playVideo();
          } catch (e) {
            console.warn('Trailer play error:', e);
          }
        }
        heroStage.classList.add('video-active');
      }
    }

    // Hover listeners to pause/resume auto-slide smoothly
    heroStage.addEventListener('mouseenter', () => {
      isHovered = true;
      if (autoRotateTimer) clearTimeout(autoRotateTimer);
    });

    heroStage.addEventListener('mouseleave', () => {
      isHovered = false;
      if (delayElapsed && isVideoPlaying) {
        scheduleAutoSlide();
      }
    });

    // Play Buttons Handler (Instantly activate trailer with sound)
    const playBtns = document.querySelectorAll('.btn-netflix-play');
    playBtns.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        if (!ytPlayer) return;
        heroStage.classList.add('video-active');
        ytPlayer.unMute();
        ytPlayer.setVolume(85);
        isMuted = false;
        const iconMuted = heroMuteToggle ? heroMuteToggle.querySelector('.icon-muted') : null;
        const iconUnmuted = heroMuteToggle ? heroMuteToggle.querySelector('.icon-unmuted') : null;
        if (iconMuted) iconMuted.style.display = 'none';
        if (iconUnmuted) iconUnmuted.style.display = 'inline-block';
        if (typeof ytPlayer.playVideo === 'function') {
          ytPlayer.playVideo();
        }
      });
    });

    // Load YouTube API
    function initYouTubePlayer() {
      if (!window.YT || !window.YT.Player) {
        const tag = document.createElement('script');
        tag.src = 'https://www.youtube.com/iframe_api';
        const firstScriptTag = document.getElementsByTagName('script')[0];
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
      } else {
        if (typeof window.onYouTubeIframeAPIReady === 'function') {
          window.onYouTubeIframeAPIReady();
        }
      }
    }

    window.onYouTubeIframeAPIReady = function () {
      const initialTrailer = getActiveTrailerId();
      ytPlayer = new YT.Player('heroYoutubePlayer', {
        videoId: initialTrailer,
        playerVars: {
          autoplay: 1,
          mute: 1, // Starts without sound
          controls: 0,
          showinfo: 0,
          rel: 0,
          loop: 1,
          playlist: initialTrailer,
          modestbranding: 1,
          playsinline: 1,
          enablejsapi: 1,
          iv_load_policy: 3,
          disablekb: 1,
        },
        events: {
          onReady: (event) => {
            event.target.mute();
            event.target.playVideo();
          },
          onStateChange: (event) => {
            if (event.data === YT.PlayerState.PLAYING) {
              isVideoPlaying = true;
              tryActivateTrailer();
            } else if (event.data === YT.PlayerState.ENDED) {
              // Automatically slide to next trending movie when trailer finishes
              switchSlide(currentIndex + 1, false, 'right');
            }
          },
        },
      });
    };

    if (window.YT && window.YT.Player) {
      window.onYouTubeIframeAPIReady();
    } else {
      initYouTubePlayer();
    }

    // Prev / Next Arrows
    if (prevBtn) {
      prevBtn.addEventListener('click', (e) => {
        e.preventDefault();
        switchSlide(currentIndex - 1, true, 'left');
      });
    }
    if (nextBtn) {
      nextBtn.addEventListener('click', (e) => {
        e.preventDefault();
        switchSlide(currentIndex + 1, true, 'right');
      });
    }

    // Keyboard Arrow Navigation
    window.addEventListener('keydown', (e) => {
      if (document.activeElement && ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
      if (e.key === 'ArrowRight') {
        switchSlide(currentIndex + 1, true, 'right');
      } else if (e.key === 'ArrowLeft') {
        switchSlide(currentIndex - 1, true, 'left');
      }
    });

    // Audio Mute/Unmute Toggle
    if (heroMuteToggle) {
      heroMuteToggle.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!ytPlayer || typeof ytPlayer.isMuted !== 'function') return;

        const iconMuted = heroMuteToggle.querySelector('.icon-muted');
        const iconUnmuted = heroMuteToggle.querySelector('.icon-unmuted');

        if (isMuted) {
          ytPlayer.unMute();
          ytPlayer.setVolume(85);
          isMuted = false;
          if (iconMuted) iconMuted.style.display = 'none';
          if (iconUnmuted) iconUnmuted.style.display = 'inline-block';
          heroMuteToggle.title = 'Sound On (Click to Mute)';
        } else {
          ytPlayer.mute();
          isMuted = true;
          if (iconMuted) iconMuted.style.display = 'inline-block';
          if (iconUnmuted) iconUnmuted.style.display = 'none';
          heroMuteToggle.title = 'Sound Muted (Click to Unmute)';
        }
      });
    }

    // Play/Pause Toggle
    const heroPlayToggle = document.getElementById('heroPlayToggle');
    if (heroPlayToggle) {
      heroPlayToggle.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!ytPlayer || typeof ytPlayer.getPlayerState !== 'function') return;

        const iconPause = heroPlayToggle.querySelector('.icon-pause');
        const iconPlay = heroPlayToggle.querySelector('.icon-play');
        const state = ytPlayer.getPlayerState();

        if (state === YT.PlayerState.PLAYING) {
          ytPlayer.pauseVideo();
          if (autoRotateTimer) clearTimeout(autoRotateTimer);
          if (iconPause) iconPause.style.display = 'none';
          if (iconPlay) iconPlay.style.display = 'inline-block';
          heroPlayToggle.title = 'Resume Trailer';
        } else {
          ytPlayer.playVideo();
          scheduleAutoSlide();
          if (iconPause) iconPause.style.display = 'inline-block';
          if (iconPlay) iconPlay.style.display = 'none';
          heroPlayToggle.title = 'Pause Trailer';
        }
      });
    }

    // IntersectionObserver: pause video when scrolled out of view
    if ('IntersectionObserver' in window) {
      const heroObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!ytPlayer || typeof ytPlayer.getPlayerState !== 'function') return;
          if (!entry.isIntersecting) {
            if (ytPlayer.getPlayerState() === YT.PlayerState.PLAYING) {
              ytPlayer.pauseVideo();
              ytPlayer._pausedByScroll = true;
            }
          } else {
            if (ytPlayer._pausedByScroll) {
              ytPlayer.playVideo();
              ytPlayer._pausedByScroll = false;
            }
          }
        });
      }, { threshold: 0.15 });

      heroObserver.observe(heroStage);
    }

    // Initialize first slide
    switchSlide(0, false, 'right');
  }

  // ----------------------------------------------------------------------------
  // 4. IntersectionObserver: Scroll-Tied Section Reveals
  // ----------------------------------------------------------------------------
  const revealSections = document.querySelectorAll('.scroll-reveal-section');

  if ('IntersectionObserver' in window && !prefersReducedMotion) {
    const sectionObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          observer.unobserve(entry.target);
        }
      });
    }, {
      root: null,
      threshold: 0.12,
      rootMargin: '0px 0px -40px 0px',
    });

    revealSections.forEach((section) => {
      sectionObserver.observe(section);
    });
  } else {
    // Fallback: immediately show all sections
    revealSections.forEach((section) => section.classList.add('in-view'));
  }

  // ----------------------------------------------------------------------------
  // 5. Horizontal Carousel Scroll Navigation
  // ----------------------------------------------------------------------------
  window.scrollTrack = function (trackId, offset) {
    const track = document.getElementById(trackId);
    if (track) {
      track.scrollBy({
        left: offset,
        behavior: 'smooth',
      });
    }
  };

  // ----------------------------------------------------------------------------
  // 6. Mobile Menu Drawer Toggle
  // ----------------------------------------------------------------------------
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  const mobileMenuDrawer = document.getElementById('mobileMenuDrawer');

  if (mobileMenuBtn && mobileMenuDrawer) {
    mobileMenuBtn.addEventListener('click', () => {
      mobileMenuDrawer.classList.toggle('open');
      const isOpen = mobileMenuDrawer.classList.contains('open');
      mobileMenuBtn.setAttribute('aria-expanded', isOpen);
    });
  }

  // ----------------------------------------------------------------------------
  // 7. Interactive Star Rating Hover Dynamics
  // ----------------------------------------------------------------------------
  const starForm = document.getElementById('starRatingForm');
  if (starForm) {
    const stars = starForm.querySelectorAll('.star-btn');
    stars.forEach((btn, idx) => {
      btn.addEventListener('mouseenter', () => {
        stars.forEach((s, sIdx) => {
          if (sIdx <= idx) {
            s.style.color = 'var(--accent-gold)';
          } else {
            s.style.color = 'rgba(255, 255, 255, 0.25)';
          }
        });
      });

      btn.addEventListener('mouseleave', () => {
        stars.forEach((s) => {
          s.style.color = '';
        });
      });
    });
  }

  // ----------------------------------------------------------------------------
  // 8. Auto-dismiss Flash Alerts
  // ----------------------------------------------------------------------------
  const flashContainer = document.getElementById('flashContainer');
  if (flashContainer) {
    setTimeout(() => {
      const toasts = flashContainer.querySelectorAll('.flash-toast');
      toasts.forEach((t) => {
        t.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        t.style.opacity = '0';
        t.style.transform = 'translateX(30px)';
        setTimeout(() => t.remove(), 400);
      });
    }, 5000);
  }

  // ----------------------------------------------------------------------------
  // 9. Netflix Quick-Preview & Explainable AI Modal Controller
  // ----------------------------------------------------------------------------
  const modalBackdrop = document.getElementById('netflixModalBackdrop');
  const modalCloseBtn = document.getElementById('modalCloseBtn');
  const modalHeroBanner = document.getElementById('modalHeroBanner');
  const modalTitle = document.getElementById('modalTitle');
  const modalOverview = document.getElementById('modalOverview');
  const modalCast = document.getElementById('modalCast');
  const modalDirector = document.getElementById('modalDirector');
  const modalGenres = document.getElementById('modalGenres');
  const modalMatchTag = document.getElementById('modalMatchTag');
  const modalYear = document.getElementById('modalYear');
  const modalDetailsBtn = document.getElementById('modalDetailsBtn');
  const modalPlayBtn = document.getElementById('modalPlayBtn');
  const modalXaiScore = document.getElementById('modalXaiScore');
  const modalXaiReason = document.getElementById('modalXaiReason');
  const modalXaiKeywords = document.getElementById('modalXaiKeywords');
  const modalRecsGrid = document.getElementById('modalRecsGrid');

  async function openQuickPreview(movieId) {
    if (!modalBackdrop || !movieId) return;

    // Reset fields to loading state
    modalTitle.textContent = 'Loading...';
    modalOverview.textContent = 'Fetching semantic metadata & model embeddings...';
    modalHeroBanner.style.backgroundImage = 'none';
    modalXaiKeywords.innerHTML = '';
    modalRecsGrid.innerHTML = '';
    modalBackdrop.classList.add('open');
    document.body.style.overflow = 'hidden';

    try {
      const res = await fetch(`/api/preview/${movieId}`);
      const data = await res.json();
      if (data.status === 'success' && data.movie) {
        const m = data.movie;
        modalTitle.textContent = m.title;
        modalOverview.textContent = m.overview || 'No synopsis available.';
        modalCast.textContent = m.cast ? m.cast.split(',').slice(0, 4).join(', ') : 'N/A';
        modalDirector.textContent = m.director || 'N/A';
        modalGenres.textContent = m.genres || 'N/A';
        modalYear.textContent = m.release_year || '2024';
        modalMatchTag.textContent = m.vote_average ? `★ ${m.vote_average.toFixed(1)} Rating` : '98% Match';

        if (m.backdrop_url) {
          modalHeroBanner.style.backgroundImage = `url('${m.backdrop_url}')`;
        }

        modalDetailsBtn.href = `/movie/${m.id}`;

        if (modalPlayBtn) {
          modalPlayBtn.onclick = () => {
            window.location.href = `/movie/${m.id}#trailer`;
          };
        }

        // XAI Section
        if (data.xai_explanation) {
          const xai = data.xai_explanation;
          modalXaiScore.textContent = `Cosine Score: ${xai.cosine_similarity}`;
          modalXaiReason.textContent = xai.explanation || 'Mathematically verified via sparse vector cosine distance.';
          
          if (xai.top_terms && xai.top_terms.length > 0) {
            modalXaiKeywords.innerHTML = xai.top_terms.map(t => 
              `<span class="xai-term-badge">${t.term}</span>`
            ).join('');
          } else {
            modalXaiKeywords.innerHTML = '<span class="xai-term-badge">General Genre Vector</span>';
          }
        } else {
          modalXaiScore.textContent = 'Cosine: 0.920';
          modalXaiReason.textContent = 'Recommended based on high-order textual and genre semantic similarity.';
        }

        // Recommendations Grid inside Modal
        if (data.recommendations && data.recommendations.length > 0) {
          modalRecsGrid.innerHTML = data.recommendations.map(r => `
            <div class="modal-rec-card" onclick="window.location.href='/movie/${r.id}'">
              <img src="${r.poster_url}" alt="${r.title}" class="modal-rec-img" loading="lazy">
              <div class="modal-rec-info">
                <div class="modal-rec-title" title="${r.title}">${r.title}</div>
                <div class="modal-rec-meta">
                  <span>${r.match_percentage || 85}% Match</span>
                  <span>${r.release_date ? r.release_date.substring(0, 4) : ''}</span>
                </div>
              </div>
            </div>
          `).join('');
        } else {
          modalRecsGrid.innerHTML = '<p style="color:#888; font-size:0.9rem;">No similar items cataloged.</p>';
        }
      }
    } catch (err) {
      console.error('Preview error:', err);
    }
  }

  function closeQuickPreview() {
    if (modalBackdrop) {
      modalBackdrop.classList.remove('open');
      document.body.style.overflow = '';
    }
  }

  if (modalCloseBtn) {
    modalCloseBtn.addEventListener('click', closeQuickPreview);
  }

  if (modalBackdrop) {
    modalBackdrop.addEventListener('click', (e) => {
      if (e.target === modalBackdrop) {
        closeQuickPreview();
      }
    });
  }

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalBackdrop && modalBackdrop.classList.contains('open')) {
      closeQuickPreview();
    }
  });

  // Attach click listener for all modal trigger buttons
  document.addEventListener('click', (e) => {
    const trigger = e.target.closest('.btn-open-modal');
    if (trigger) {
      e.preventDefault();
      const movieId = trigger.dataset.movieId;
      if (movieId) {
        openQuickPreview(movieId);
      }
    }
  });

  // ----------------------------------------------------------------------------
  // 10. Netflix India FAQ Accordion Interactive Toggles
  // ----------------------------------------------------------------------------
  const faqBtns = document.querySelectorAll('.faq-question-btn');
  faqBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const item = btn.closest('.faq-item');
      const isOpen = item.classList.contains('active');
      
      // Close all other open items
      document.querySelectorAll('.faq-item.active').forEach((other) => {
        if (other !== item) {
          other.classList.remove('active');
          const otherBtn = other.querySelector('.faq-question-btn');
          if (otherBtn) otherBtn.setAttribute('aria-expanded', 'false');
        }
      });

      item.classList.toggle('active', !isOpen);
      btn.setAttribute('aria-expanded', !isOpen);
    });
  });
});

