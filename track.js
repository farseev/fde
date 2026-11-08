/* faithdriven.sg — GA4 events for every call to action. Loaded on every page.
   KEY EVENTS (mark in GA4 > Admin > Events; recurring_donation_complete is the primary one):
     recurring_donation_complete  /thank-you-giving/ after a Stripe monthly gift
     recurring_donation_start     a monthly tier or "Give monthly" opens Stripe checkout
     gathering_register           Eventbrite registration for a gathering / Foundation session
     group_join                   "Register with FDE" / "Find your people" (FDE groups sign-up)
     contact_click                WhatsApp or email to the team
   FUNNEL / OTHER: donate_view, donation_frequency_select (monthly | one_off),
     donation_amount_select, one_off_donation_enquiry, community_join (WhatsApp group),
     video_play, social_click.
   Nothing here sets cookies. */
(function () {
  'use strict';
  function ev(n, p) { try { if (window.gtag) window.gtag('event', n, p || {}); } catch (e) {} }
  window.fdeTrack = ev;
  var lang = (document.documentElement.lang || 'en').slice(0, 2);
  function amt(h) { var m = /fde-(\d+)/.exec(h || ''); return m ? +m[1] : null; }
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest && e.target.closest('a'); if (!a) return;
    var h = a.getAttribute('href') || '';
    var where = a.closest('#give') ? 'give' : (a.closest('footer') ? 'footer' : (a.closest('header,nav') ? 'header' : 'page'));
    var n = amt(h);
    if (n) {
      if (a.classList.contains('tier')) ev('donation_amount_select', { amount: n, frequency: 'monthly', currency: 'SGD' });
      ev('donation_frequency_select', { frequency: 'monthly', link_location: where });
      ev('recurring_donation_start', { amount: n, value: n, currency: 'SGD', method: a.classList.contains('tier') ? 'tier' : 'button', link_location: where, language: lang });
      try { localStorage.setItem('fde_gift', String(n)); } catch (_) {}
      return;
    }
    if (/#give$/.test(h)) { ev('donate_click', { link_location: where }); return; }
    if (/wa\.me\//.test(h)) {
      if (a.closest('.give-note')) {
        ev('donation_frequency_select', { frequency: 'one_off', link_location: where });
        ev('one_off_donation_enquiry', { language: lang });
      } else ev('contact_click', { method: 'whatsapp', link_location: where });
      return;
    }
    if (/^mailto:/.test(h)) { ev('contact_click', { method: 'email', link_location: where }); return; }
    if (/share\.somin\.ai\/event-fde|eventbrite\./.test(h)) { ev('gathering_register', { link_location: where, language: lang }); return; }
    if (/share\.somin\.ai\/fde$|groups\.faithdrivenentrepreneur\.org/.test(h)) { ev('group_join', { link_location: where, language: lang }); return; }
    if (/chat\.whatsapp\.com/.test(h)) { ev('community_join', { link_location: where }); return; }
    if (/youtube\.com|instagram\.com|facebook\.com|linkedin\.com|podcasts\.apple\.com|spotify\.com/.test(h)) {
      ev('social_click', { destination: h.replace(/^https?:\/\//, '').split('/')[0], link_location: where });
    }
  }, true);
  document.addEventListener('click', function (e) {
    var v = e.target && e.target.closest && e.target.closest('.video[data-id]');
    if (v) ev('video_play', { video_id: v.getAttribute('data-id') });
  }, true);
  function ready(fn) { if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn); else fn(); }
  ready(function () {
    var g = document.getElementById('give');
    if (g && 'IntersectionObserver' in window) {
      var o = new IntersectionObserver(function (es) {
        es.forEach(function (x) { if (x.isIntersecting) { ev('donate_view', { arrived_by: /#give/.test(location.hash) ? 'link' : 'scroll' }); o.disconnect(); } });
      }, { threshold: 0.3 });
      o.observe(g);
    }
  });
})();
