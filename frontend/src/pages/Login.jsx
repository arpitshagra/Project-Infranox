import React, { useState } from 'react';

export default function Login({ onLoginSuccess, onCancel }) {
  const [isSignUp, setIsSignUp] = useState(false);
  const [role, setRole] = useState('municipal'); // 'municipal' | 'engineer' | 'citizen'
  const [email, setEmail] = useState('inspector@infranox.gov.in');
  const [password, setPassword] = useState('••••••••••••');
  const [name, setName] = useState('Arjun Mehta');
  const [department, setDepartment] = useState('Central Road Research Institute (CRRI)');

  const handleSubmit = (e) => {
    e.preventDefault();
    const userProfile = {
      name: isSignUp ? name : (email.split('@')[0] || 'User'),
      email,
      role,
      department: role === 'citizen' ? 'Verified Citizen' : department,
      token: 'demo-jwt-' + Math.random().toString(36).substring(2, 9)
    };
    localStorage.setItem('infranox_user', JSON.stringify(userProfile));
    onLoginSuccess(userProfile);
  };

  const handleDemoLogin = (selectedRole) => {
    const rolesMap = {
      municipal: { name: 'Arjun Mehta', email: 'inspector@delhi.gov.in', dept: 'Pavement Quality Division' },
      engineer: { name: 'Dr. Priya Sharma', email: 'priya.crri@gov.in', dept: 'Highway Engineering Cell' },
      citizen: { name: 'Rohan Gupta', email: 'rohan.g@gmail.com', dept: 'Public Inspector' }
    };
    const sel = rolesMap[selectedRole];
    const userProfile = {
      name: sel.name,
      email: sel.email,
      role: selectedRole,
      department: sel.dept,
      token: 'demo-token-' + selectedRole
    };
    localStorage.setItem('infranox_user', JSON.stringify(userProfile));
    onLoginSuccess(userProfile);
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6">
      <div className="w-full max-w-md bg-white border border-slate-200 rounded-xl p-8 shadow-sm">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Department Portal
            </span>
            {onCancel && (
              <button 
                onClick={onCancel}
                className="text-xs text-slate-400 hover:text-slate-700"
              >
                Back to Platform
              </button>
            )}
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
            {isSignUp ? 'Create Officer Account' : 'Sign in to INFRANOX'}
          </h2>
          <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
            Access civil pavement condition surveys, neural defect maps, and municipal grievance queues.
          </p>
        </div>

        {/* Quick Demo Role Switcher */}
        <div className="mb-6 p-3 bg-slate-50 rounded-lg border border-slate-200">
          <span className="text-[11px] font-semibold text-slate-600 block mb-2">
            One-Click Demo Access:
          </span>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => handleDemoLogin('municipal')}
              className="py-1.5 px-2 bg-white border border-slate-200 hover:border-slate-400 rounded text-[11px] font-medium text-slate-800 transition"
            >
              Municipal Officer
            </button>
            <button
              type="button"
              onClick={() => handleDemoLogin('engineer')}
              className="py-1.5 px-2 bg-white border border-slate-200 hover:border-slate-400 rounded text-[11px] font-medium text-slate-800 transition"
            >
              Civil Engineer
            </button>
            <button
              type="button"
              onClick={() => handleDemoLogin('citizen')}
              className="py-1.5 px-2 bg-white border border-slate-200 hover:border-slate-400 rounded text-[11px] font-medium text-slate-800 transition"
            >
              Citizen User
            </button>
          </div>
        </div>

        {/* Auth Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Access Role
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full text-xs font-medium border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-1 focus:ring-slate-900"
            >
              <option value="municipal">Municipal Road Authority (MRA)</option>
              <option value="engineer">Highway Safety & Civil Inspector</option>
              <option value="citizen">Public Citizen Reporter</option>
            </select>
          </div>

          {isSignUp && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Full Name
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Arjun Mehta"
                className="w-full text-xs font-medium border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-1 focus:ring-slate-900"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@infranox.gov.in"
              className="w-full text-xs font-medium border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-1 focus:ring-slate-900"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-700">
                Password
              </label>
              {!isSignUp && (
                <span className="text-[11px] text-slate-500 hover:text-slate-800 cursor-pointer">
                  Forgot password?
                </span>
              )}
            </div>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full text-xs font-medium border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-1 focus:ring-slate-900"
            />
          </div>

          <button
            type="submit"
            className="w-full mt-2 py-2.5 px-4 bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs rounded-lg transition"
          >
            {isSignUp ? 'Register Credential' : 'Authenticate Session'}
          </button>
        </form>

        {/* Toggle Sign Up / Login */}
        <div className="mt-6 pt-6 border-t border-slate-100 text-center">
          <p className="text-xs text-slate-500">
            {isSignUp ? 'Already registered with municipal department?' : "Don't have an inspector account?"}{' '}
            <button
              type="button"
              onClick={() => setIsSignUp(!isSignUp)}
              className="font-semibold text-slate-900 hover:underline"
            >
              {isSignUp ? 'Sign in' : 'Request Access'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

