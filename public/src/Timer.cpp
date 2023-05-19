//
// Timer.cpp
//
// $Id: //poco/1.4/Foundation/src/Timer.cpp#1 $
//
// Library: Foundation
// Package: Threading
// Module:  Timer
//
// Copyright (c) 2004-2006, Applied Informatics Software Engineering GmbH.
// and Contributors.
//
// Permission is hereby granted, free of charge, to any person or organization
// obtaining a copy of the software and accompanying documentation covered by
// this license (the "Software") to use, reproduce, display, distribute,
// execute, and transmit the Software, and to prepare derivative works of the
// Software, and to permit third-parties to whom the Software is furnished to
// do so, all subject to the following:
// 
// The copyright notices in the Software and this entire statement, including
// the above license grant, this restriction and the following disclaimer,
// must be included in all copies of the Software, in whole or in part, and
// all derivative works of the Software, unless such copies or derivative
// works are solely in the form of machine-executable object code generated by
// a source language processor.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO EVENT
// SHALL THE COPYRIGHT HOLDERS OR ANYONE DISTRIBUTING THE SOFTWARE BE LIABLE
// FOR ANY DAMAGES OR OTHER LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE,
// ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
// DEALINGS IN THE SOFTWARE.
//


#include "Poco/Timer.h"
#include "Poco/ThreadPool.h"
#include "Poco/Exception.h"
#include "Poco/ErrorHandler.h"


namespace Poco {


Timer::Timer(long startInterval, long periodicInterval): 
	_startInterval(startInterval), 
	_periodicInterval(periodicInterval),
	_skipped(0),
	_pCallback(0)
{
	poco_assert (startInterval >= 0 && periodicInterval >= 0);
}


Timer::~Timer()
{
	stop();
}


void Timer::start(const AbstractTimerCallback& method)
{
	start(method, Thread::PRIO_NORMAL_, ThreadPool::defaultPool());
}


void Timer::start(const AbstractTimerCallback& method, Thread::Priority priority)
{
	start(method, priority, ThreadPool::defaultPool());
}


void Timer::start(const AbstractTimerCallback& method, ThreadPool& threadPool)
{
	start(method, Thread::PRIO_NORMAL_, threadPool);
}


void Timer::start(const AbstractTimerCallback& method, Thread::Priority priority, ThreadPool& threadPool)
{
	Timestamp nextInvocation;
	nextInvocation += static_cast<Timestamp::TimeVal>(_startInterval)*1000;

	poco_assert (!_pCallback);

	FastMutex::ScopedLock lock(_mutex);	
	_nextInvocation = nextInvocation;
	_pCallback = method.clone();
	_wakeUp.reset();
	threadPool.startWithPriority(priority, *this);
}


void Timer::stop()
{
	FastMutex::ScopedLock lock(_mutex);
	if (_pCallback)
	{
		_periodicInterval = 0;
		_mutex.unlock();
		_wakeUp.set();
		_done.wait(); // warning: deadlock if called from timer callback
		_mutex.lock();
		delete _pCallback;
		_pCallback = 0;
	}
}


void Timer::restart()
{
	FastMutex::ScopedLock lock(_mutex);
	if (_pCallback)
	{
		_wakeUp.set();
	}
}


void Timer::restart(long milliseconds)
{
	poco_assert (milliseconds >= 0);
	FastMutex::ScopedLock lock(_mutex);
	if (_pCallback)
	{
		_periodicInterval = milliseconds;
		_wakeUp.set();
	}
}


long Timer::getStartInterval() const
{
	FastMutex::ScopedLock lock(_mutex);
	return _startInterval;
}


void Timer::setStartInterval(long milliseconds)
{
	poco_assert (milliseconds >= 0);
	FastMutex::ScopedLock lock(_mutex);
	_startInterval = milliseconds;
}


long Timer::getPeriodicInterval() const
{
	FastMutex::ScopedLock lock(_mutex);
	return _periodicInterval;
}


void Timer::setPeriodicInterval(long milliseconds)
{
	poco_assert (milliseconds >= 0);
	FastMutex::ScopedLock lock(_mutex);
	_periodicInterval = milliseconds;
}


void Timer::run()
{
	Poco::Timestamp now;
	long interval(0);
	do
	{
		long sleep(0);
		do
		{
			now.update();
			sleep = static_cast<long>((_nextInvocation - now)/1000);
			if (sleep < 0)
			{
				if (interval == 0)
				{
					sleep = 0;
					break;
				}
				_nextInvocation += static_cast<Timestamp::TimeVal>(interval)*1000;
				++_skipped;
			}
		}
		while (sleep < 0);

		if (_wakeUp.tryWait(sleep))
		{
			Poco::FastMutex::ScopedLock lock(_mutex);
			_nextInvocation.update();
			interval = _periodicInterval;
		}
		else
		{
			try
			{
				_pCallback->invoke(*this);
			}
			catch (Poco::Exception& exc)
			{
				Poco::ErrorHandler::handle(exc);
			}
			catch (std::exception& exc)
			{
				Poco::ErrorHandler::handle(exc);
			}
			catch (...)
			{
				Poco::ErrorHandler::handle();
			}
			interval = _periodicInterval;
		}
		_nextInvocation += static_cast<Timestamp::TimeVal>(interval)*1000;
		_skipped = 0;
	}
	while (interval > 0);
	_done.set();
}


long Timer::skipped() const
{
	return _skipped;
}


AbstractTimerCallback::AbstractTimerCallback()
{
}


AbstractTimerCallback::AbstractTimerCallback(const AbstractTimerCallback& callback)
{
}


AbstractTimerCallback::~AbstractTimerCallback()
{
}


AbstractTimerCallback& AbstractTimerCallback::operator = (const AbstractTimerCallback& callback)
{
	return *this;
}


} // namespace Poco
