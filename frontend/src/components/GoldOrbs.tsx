/** Фоновые полупрозрачные золотые круги с медленным дрейфом. */
export function GoldOrbs() {
  const orbs = [
    { className: 'left-[6%] top-[12%] h-40 w-40 animate-drift', delay: '0s' },
    { className: 'right-[8%] top-[22%] h-56 w-56 animate-drift', delay: '2.5s' },
    { className: 'left-[18%] bottom-[16%] h-48 w-48 animate-drift', delay: '5s' },
    { className: 'right-[18%] bottom-[8%] h-32 w-32 animate-drift', delay: '1.2s' },
    { className: 'left-[45%] top-[40%] h-24 w-24 animate-drift', delay: '3.8s' },
  ];

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 overflow-hidden"
    >
      {orbs.map((orb) => (
        <span
          key={orb.className}
          className={`absolute rounded-full bg-gold-400/15 blur-2xl ${orb.className}`}
          style={{ animationDelay: orb.delay }}
        />
      ))}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_35%,rgba(11,9,7,0.55)_100%)]" />
    </div>
  );
}
